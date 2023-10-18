import warnings
from ast import literal_eval
from datetime import datetime
from io import BytesIO, StringIO
from typing import Tuple, Optional, Union, Sequence, Dict
from zipfile import ZipFile
from pathlib import Path

from biopsykit.io.io import _sanitize_index_cols, _apply_index_cols
from biopsykit.io.nilspod import _handle_counter_inconsistencies_session
from biopsykit.io.saliva import (
    _check_num_samples,
    _apply_condition_list,
    _get_id_columns,
    _check_sample_times,
    _get_condition_col,
    _get_index_cols,
)
from biopsykit.io.sleep_analyzer import (
    WITHINGS_RAW_DATA_SOURCES,
    _localize_time,
    _explode_timestamp,
    _reindex_datetime_index,
)
from biopsykit.sleep.utils import split_nights
from biopsykit.utils._datatype_validation_helper import (
    _assert_file_extension,
    _assert_has_columns,
)
from biopsykit.utils.dataframe_handling import convert_nan
from biopsykit.utils.datatype_helper import (
    SalivaRawDataFrame,
    is_saliva_raw_dataframe,
    _SalivaRawDataFrame,
    SubjectConditionDataFrame,
    SubjectConditionDict,
    is_subject_condition_dict,
    is_subject_condition_dataframe,
    _SubjectConditionDataFrame,
)
from biopsykit.utils.time import tz

import numpy as np
import pandas as pd
from nilspodlib import Dataset
from nilspodlib.utils import path_t
from typing_extensions import Literal

from src.Physiological.AdaptedNilspod import SyncedSessionAdapted, NilsPodAdapted

COUNTER_INCONSISTENCY_HANDLING = Literal["raise", "warn", "ignore"]
_DATA_COL_NAMES = {"cortisol": "cortisol (nmol/l)", "amylase": "amylase (U/ml)"}


def get_datetime_columns_of_data_frame(df: pd.DataFrame):
    df_type = df.dtypes.rename_axis("column").to_frame("dtype").reset_index(drop=False)
    df_type["dtype_str"] = df_type["dtype"].map(str)
    dt_cols = df_type[df_type["dtype_str"].str.contains("datetime64")][
        "column"
    ].tolist()
    if isinstance(df.index, pd.DatetimeIndex):
        dt_cols.append("index")
    return dt_cols


def get_start_and_end_time(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    datetime_columns = get_datetime_columns_of_data_frame(df)
    if "index" in datetime_columns:
        start = pd.to_datetime(df.index.values.min())
        end = pd.to_datetime(df.index.values.max())
        return (start, end)
    elif len(datetime_columns) == 1:
        start = df[datetime_columns[0]].min()
        end = df[datetime_columns[0]].max()
        return (start, end)
    return None


def timezone_aware_to_naive(dt: datetime) -> datetime:
    naive = datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
        tzinfo=None,
    )
    return naive


def _handle_counter_inconsistencies_dataset(
    dataset: Dataset,
    handle_counter_inconsistency: COUNTER_INCONSISTENCY_HANDLING,
):
    idxs_corrupted = np.where(np.diff(dataset.counter) < 1)[0]
    # edge case: check if only last sample is corrupted. if yes, cut last sample
    if len(idxs_corrupted) == 1 and (idxs_corrupted == len(dataset.counter) - 2):
        dataset.cut(start=0, stop=idxs_corrupted[0], inplace=True)
    elif len(idxs_corrupted) > 1:
        if handle_counter_inconsistency == "raise":
            raise ValueError(
                "Error loading dataset. Counter not monotonously increasing!"
            )
        if handle_counter_inconsistency == "warn":
            warnings.warn(
                "Counter not monotonously increasing. This might indicate that the dataset is corrupted or "
                "that the dataset was recorded as part of a synchronized session and might need to be loaded "
                "using `biopsykit.io.nilspod.load_synced_session_nilspod()`. "
                "Check the counter of the DataFrame manually!"
            )


def load_synced_session_nilspod_zip(
    file: ZipFile,
    datastreams: Optional[Union[str, Sequence[str]]] = None,
    handle_counter_inconsistency: Optional[COUNTER_INCONSISTENCY_HANDLING] = "raise",
    **kwargs,
) -> Tuple[pd.DataFrame, float]:

    nilspod_files = list(
        filter(lambda file_name: file_name.endswith(".bin"), file.namelist())
    )
    if len(nilspod_files) == 0:
        raise ValueError("No NilsPod files found in Zipfile!")

    kwargs.setdefault("tz", kwargs.pop("timezone", tz))
    session = SyncedSessionAdapted.from_folder_path(file, **kwargs)

    # Ab hier standard
    session.align_to_syncregion(inplace=True)

    _handle_counter_inconsistencies_session(session, handle_counter_inconsistency)
    if isinstance(datastreams, str):
        datastreams = [datastreams]

    # convert dataset to dataframe and localize timestamp
    df = session.data_as_df(datastreams, index="local_datetime", concat_df=True)
    df.index.name = "time"
    if len(set(session.info.sampling_rate_hz)) > 1:
        raise ValueError(
            f"Datasets in the sessions have different sampling rates! Got: {session.info.sampling_rate_hz}."
        )
    fs = session.info.sampling_rate_hz[0]
    return df, fs


def load_dataset_nilspod_zip(
    zip_file: Optional[ZipFile] = None,
    file_path: Optional[str] = None,
    dataset: Optional[Dataset] = None,
    datastreams: Optional[Union[str, Sequence[str]]] = None,
    handle_counter_inconsistency: Optional[COUNTER_INCONSISTENCY_HANDLING] = "raise",
    **kwargs,
) -> Tuple[pd.DataFrame, float]:
    if zip_file is not None:
        _assert_file_extension(file_path, ".bin")
        kwargs.setdefault("tz", kwargs.pop("timezone", tz))
        kwargs.setdefault("legacy_support", "resolve")
        dataset = NilsPodAdapted.from_bin_file(
            BytesIO(zip_file.read(file_path)), **kwargs
        )

    if file_path is None and dataset is None:
        raise ValueError(
            "Either 'file_path' or 'dataset' must be supplied as parameter!"
        )

    _handle_counter_inconsistencies_dataset(dataset, handle_counter_inconsistency)

    if isinstance(datastreams, str):
        datastreams = [datastreams]

    # convert dataset to dataframe and localize timestamp
    df = dataset.data_as_df(datastreams, index="local_datetime")
    df.index.name = "time"
    return df, dataset.info.sampling_rate_hz


def load_folder_nilspod_zip(
    file: ZipFile, phase_names: Optional[Sequence[str]] = None, **kwargs
) -> Tuple[Dict[str, pd.DataFrame], float]:
    dataset_list = list(
        filter(lambda file_name: file_name.endswith(".bin"), file.namelist())
    )
    if len(dataset_list) == 0:
        raise ValueError(f"No NilsPod files found in Zipfile!")
    if phase_names is None:
        phase_names = [f"Part{i}" for i in range(len(dataset_list))]

    if len(phase_names) != len(dataset_list):
        raise ValueError(
            f"Number of phases does not match number of datasets in the folder! "
            f"Expected {len(dataset_list)}, got {len(phase_names)}."
        )

    dataset_list = [
        load_dataset_nilspod_zip(file_path=dataset_path, zip_file=file, **kwargs)
        for dataset_path in dataset_list
    ]

    # check if sampling rate is equal for all datasets in folder
    fs_list = [fs for df, fs in dataset_list]

    if len(set(fs_list)) > 1:
        raise ValueError(
            f"Datasets in the sessions have different sampling rates! Got: {fs_list}."
        )
    fs = fs_list[0]

    dataset_dict = {phase: df for phase, (df, fs) in zip(phase_names, dataset_list)}
    return dataset_dict, fs


def _load_dataframe(
    filepath_or_buffer: Path | bytes,
    file_name: Optional[str] = None,
    **kwargs,
):
    if type(filepath_or_buffer) is not bytes:
        if filepath_or_buffer.suffix in [".csv"]:
            return pd.read_csv(filepath_or_buffer, **kwargs)
        return pd.read_excel(filepath_or_buffer, **kwargs)
    else:
        if file_name is None:
            raise ValueError(
                "If 'file' is of type BytesIO, 'file_name' must be supplied as parameter!"
            )
        if file_name.endswith(".csv"):
            return pd.read_csv(StringIO(filepath_or_buffer.decode("utf8")), **kwargs)
        return pd.read_excel(filepath_or_buffer, **kwargs)


def load_questionnaire_data(
    file: bytes | path_t,
    file_name: Optional[str] = None,
    subject_col: Optional[str] = None,
    condition_col: Optional[str] = None,
    additional_index_cols: Optional[Union[str, Sequence[str]]] = None,
    replace_missing_vals: Optional[bool] = True,
    remove_nan_rows: Optional[bool] = True,
    sheet_name: Optional[Union[str, int]] = 0,
    **kwargs,
) -> pd.DataFrame:
    if type(file) == bytes:
        file_path = Path(file_name)
    else:
        file_path = Path(file)
        file = file_path
    _assert_file_extension(file_path, expected_extension=[".xls", ".xlsx", ".csv"])
    if file_path.suffix != ".csv":
        kwargs["sheet_name"] = sheet_name
    data = _load_dataframe(file, file_name, **kwargs)
    data, index_cols = _sanitize_index_cols(
        data, subject_col, condition_col, additional_index_cols
    )
    data = _apply_index_cols(data, index_cols=index_cols)
    if replace_missing_vals:
        data = convert_nan(data)
    if remove_nan_rows:
        data = data.dropna(how="all")
    return data


def load_saliva_plate(
    file: pd.DataFrame | path_t,
    saliva_type: str,
    sample_id_col: Optional[str] = None,
    data_col: Optional[str] = None,
    id_col_names: Optional[Sequence[str]] = None,
    regex_str: Optional[str] = None,
    sample_times: Optional[Sequence[int]] = None,
    condition_list: Optional[Union[Sequence, Dict[str, Sequence], pd.Index]] = None,
    **kwargs,
) -> SalivaRawDataFrame:

    if type(file) != pd.DataFrame:
        file = Path(file)
        _assert_file_extension(file, (".xls", ".xlsx"))

    # TODO add remove_nan option (all or any)
    if regex_str is None:
        regex_str = r"(Vp\d+) (S\w)"

    if sample_id_col is None:
        sample_id_col = "sample ID"

    if data_col is None:
        data_col = _DATA_COL_NAMES[saliva_type]

    if type(file) == pd.DataFrame:
        df_saliva = file[[sample_id_col, data_col]].copy()
    else:
        df_saliva = pd.read_excel(
            file, skiprows=2, usecols=[sample_id_col, data_col], **kwargs
        )
    cols = df_saliva[sample_id_col].str.extract(regex_str).copy()
    id_col_names = _get_id_columns(id_col_names, cols)

    df_saliva[id_col_names] = cols

    df_saliva = df_saliva.drop(columns=[sample_id_col], errors="ignore")
    df_saliva = df_saliva.rename(columns={data_col: saliva_type})
    df_saliva = df_saliva.set_index(id_col_names)

    if condition_list is not None:
        df_saliva = _apply_condition_list(df_saliva, condition_list)

    num_subjects = len(df_saliva.index.get_level_values("subject").unique())

    _check_num_samples(len(df_saliva), num_subjects)

    if sample_times:
        _check_sample_times(len(df_saliva), num_subjects, sample_times)
        df_saliva["time"] = np.array(sample_times * num_subjects)

    try:
        df_saliva[saliva_type] = df_saliva[saliva_type].astype(float)
    except ValueError as e:
        raise ValueError(
            """Error converting all saliva values into numbers: '{}'
            Please check your saliva values whether there is any text etc. in the column '{}'
            and delete the values or replace them by NaN!""".format(
                e, data_col
            )
        ) from e

    is_saliva_raw_dataframe(df_saliva, saliva_type)

    return _SalivaRawDataFrame(df_saliva)


def load_saliva_wide_format(
    file: pd.DataFrame | path_t,
    saliva_type: str,
    subject_col: Optional[str] = None,
    condition_col: Optional[str] = None,
    additional_index_cols: Optional[Union[str, Sequence[str]]] = None,
    sample_times: Optional[Sequence[int]] = None,
    **kwargs,
) -> SalivaRawDataFrame:
    """Load saliva data that is in wide-format from csv file.

    It will return a `SalivaRawDataFrame`, a long-format dataframe that complies with BioPsyKit's naming convention,
    i.e., the subject ID index will be named ``subject``, the sample index will be names ``sample``,
    and the value column will be named after the saliva biomarker type.

    Parameters
    ----------
    file_path: :class:`~pathlib.Path` or str
        path to file
    saliva_type: str
        saliva type to load from file. Example: ``cortisol``
    subject_col: str, optional
        name of column containing subject IDs or ``None`` to use the default column name ``subject``.
        According to BioPsyKit's convention, the subject ID column is expected to have the name ``subject``.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: ``None``
    condition_col : str, optional
        name of the column containing condition assignments or ``None`` if no conditions are present.
        According to BioPsyKit's convention, the condition column is expected to have the name ``condition``.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: ``None``
    additional_index_cols : str or list of str, optional
        additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
        strings to indicate column name(s) that should be used as index level(s),
        or ``None`` for no additional index levels. Default: ``None``
    sample_times: list of int, optional
        times at which saliva samples were collected or ``None`` if no sample times should be specified.
        Default: ``None``
    **kwargs
        Additional parameters that are passed to :func:`pandas.read_csv` or :func:`pandas.read_excel`

    Returns
    -------
    data : :class:`~biopsykit.utils.datatype_helper.SalivaRawDataFrame`
        saliva data in `SalivaRawDataFrame` format

    Raises
    ------
    :exc:`~biopsykit.utils.exceptions.FileExtensionError`
        if file is no csv or Excel file

    """
    # ensure pathlib
    if type(file) != pd.DataFrame:
        file = Path(file)
        _assert_file_extension(file, (".xls", ".xlsx"))
        data = _load_dataframe(file, **kwargs)
    else:
        data = file

    if subject_col is None:
        subject_col = "subject"

    _assert_has_columns(data, [[subject_col]])

    if subject_col != "subject":
        # rename column
        data = data.rename(columns={subject_col: "subject"})
        subject_col = "subject"

    index_cols = [subject_col]

    data, condition_col = _get_condition_col(data, condition_col)

    index_cols = _get_index_cols(condition_col, index_cols, additional_index_cols)
    data = _apply_index_cols(data, index_cols=index_cols)

    num_subjects = len(data)
    data.columns = pd.MultiIndex.from_product(
        [[saliva_type], data.columns], names=[None, "sample"]
    )
    data = data.stack()

    _check_num_samples(len(data), num_subjects)

    if sample_times is not None:
        _check_sample_times(len(data), num_subjects, sample_times)
        data["time"] = np.array(sample_times * num_subjects)

    is_saliva_raw_dataframe(data, saliva_type)

    return _SalivaRawDataFrame(data)


def load_subject_condition_list(
    file: bytes | path_t,
    file_name: Optional[str] = None,
    subject_col: Optional[str] = None,
    condition_col: Optional[str] = None,
    return_dict: Optional[bool] = False,
    **kwargs,
) -> Union[SubjectConditionDataFrame, SubjectConditionDict]:
    """Load subject condition assignment from file.

    This function can be used to load a file that contains the assignment of subject IDs to study conditions.
    It will return a dataframe or a dictionary that complies with BioPsyKit's naming convention, i.e.,
    the subject ID index will be named ``subject`` and the condition column will be named ``condition``.

    Parameters
    ----------
    file_path : :class:`~pathlib.Path` or str
        path to time log file. Must either be an Excel or csv file
    subject_col : str, optional
        name of column containing subject IDs or ``None`` to use default column name ``subject``.
        According to BioPsyKit's convention, the subject ID column is expected to have the name ``subject``.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    condition_col : str, optional
        name of column containing condition assignments or ``None`` to use default column name ``condition``.
        According to BioPsyKit's convention, the condition column is expected to have the name ``condition``.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    return_dict : bool, optional
        whether to return a dict with subject IDs per condition (``True``) or a dataframe (``False``).
        Default: ``False``
    **kwargs
        Additional parameters that are passed tos :func:`pandas.read_csv` or :func:`pandas.read_excel`

    Returns
    -------
    :class:`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame` or
    :class:`~biopsykit.utils.datatype_helper.SubjectConditionDict`
        a standardized pandas dataframe with subject IDs and condition assignments (if ``return_dict`` is ``False``) or
        a standardized dict with subject IDs per group (if ``return_dict`` is ``True``)

    Raises
    ------
    :exc:`~biopsykit.utils.exceptions.FileExtensionError`
        if file is not a csv or Excel file
    :exc:`~biopsykit.utils.exceptions.ValidationError`
        if result is not a :class:`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame` or a
        :class:`~biopsykit.utils.datatype_helper.SubjectConditionDict`

    """
    # ensure pathlib
    if type(file) == bytes:
        file_path = Path(file_name)
    else:
        file_path = Path(file)
        file = file_path
    _assert_file_extension(file_path, expected_extension=[".xls", ".xlsx", ".csv"])

    data = _load_dataframe(file, file_name, **kwargs)

    if subject_col is None:
        subject_col = "subject"

    if condition_col is None:
        condition_col = "condition"

    _assert_has_columns(data, [[subject_col, condition_col]])

    if subject_col != "subject":
        # rename column
        subject_col = {subject_col: "subject"}
        data = data.rename(columns=subject_col)
        subject_col = "subject"

    if condition_col != "condition":
        # rename column
        condition_col = {condition_col: "condition"}
        data = data.rename(columns=condition_col)
        condition_col = "condition"
    data = data.set_index(subject_col)

    if return_dict:
        data = data.groupby(condition_col).groups
        is_subject_condition_dict(data)
        return data
    is_subject_condition_dataframe(data)
    return _SubjectConditionDataFrame(data)


# def load_saliva_wide_format(
#     file: bytes | path_t,
#     saliva_type: str,
#     file_name: Optional[str] = None,
#     subject_col: Optional[str] = None,
#     condition_col: Optional[str] = None,
#     additional_index_cols: Optional[Union[str, Sequence[str]]] = None,
#     sample_times: Optional[Sequence[int]] = None,
#     **kwargs,
# ) -> SalivaRawDataFrame:
#     """Load saliva data that is in wide-format from csv file.
#
#     It will return a `SalivaRawDataFrame`, a long-format dataframe that complies with BioPsyKit's naming convention,
#     i.e., the subject ID index will be named ``subject``, the sample index will be names ``sample``,
#     and the value column will be named after the saliva biomarker type.
#
#     Parameters
#     ----------
#     file_path: :class:`~pathlib.Path` or str
#         path to file
#     saliva_type: str
#         saliva type to load from file. Example: ``cortisol``
#     subject_col: str, optional
#         name of column containing subject IDs or ``None`` to use the default column name ``subject``.
#         According to BioPsyKit's convention, the subject ID column is expected to have the name ``subject``.
#         If the subject ID column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: ``None``
#     condition_col : str, optional
#         name of the column containing condition assignments or ``None`` if no conditions are present.
#         According to BioPsyKit's convention, the condition column is expected to have the name ``condition``.
#         If the condition column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: ``None``
#     additional_index_cols : str or list of str, optional
#         additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
#         strings to indicate column name(s) that should be used as index level(s),
#         or ``None`` for no additional index levels. Default: ``None``
#     sample_times: list of int, optional
#         times at which saliva samples were collected or ``None`` if no sample times should be specified.
#         Default: ``None``
#     **kwargs
#         Additional parameters that are passed to :func:`pandas.read_csv` or :func:`pandas.read_excel`
#
#     Returns
#     -------
#     data : :class:`~biopsykit.utils.datatype_helper.SalivaRawDataFrame`
#         saliva data in `SalivaRawDataFrame` format
#
#     Raises
#     ------
#     :exc:`~biopsykit.utils.exceptions.FileExtensionError`
#         if file is no csv or Excel file
#
#     """
#     # ensure pathlib
#     if type(file) == bytes:
#         file_path = Path(file_name)
#     else:
#         file_path = Path(file)
#         file = file_path
#     _assert_file_extension(file_path, expected_extension=[".xls", ".xlsx", ".csv"])
#     data = _load_dataframe(file, file_name, **kwargs)
#
#     if subject_col is None:
#         subject_col = "subject"
#
#     _assert_has_columns(data, [[subject_col]])
#
#     if subject_col != "subject":
#         # rename column
#         data = data.rename(columns={subject_col: "subject"})
#         subject_col = "subject"
#
#     index_cols = [subject_col]
#
#     data, condition_col = _get_condition_col(data, condition_col)
#
#     index_cols = _get_index_cols(condition_col, index_cols, additional_index_cols)
#     data = _apply_index_cols(data, index_cols=index_cols)
#
#     num_subjects = len(data)
#     data.columns = pd.MultiIndex.from_product(
#         [[saliva_type], data.columns], names=[None, "sample"]
#     )
#     data = data.stack()
#
#     _check_num_samples(len(data), num_subjects)
#
#     if sample_times is not None:
#         _check_sample_times(len(data), num_subjects, sample_times)
#         data["time"] = np.array(sample_times * num_subjects)
#
#     is_saliva_raw_dataframe(data, saliva_type)
#
#     return _SalivaRawDataFrame(data)


def load_withings_sleep_analyzer_raw_file(
    file: bytes | path_t,
    data_source: str,
    timezone: Optional[Union[type(datetime.tzinfo), str]] = None,
    split_into_nights: Optional[bool] = True,
    file_name: Optional[str] = None,
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Load single Withings Sleep Analyzer raw data file and convert into time-series data.

    Parameters
    ----------
    file : :class:`~pathlib.Path` or str
        path to file
    data_source : str
        data source of file specified by ``file_path``. Must be one of
        ['heart_rate', 'respiration_rate', 'sleep_state', 'snoring'].
    timezone : str or :class:`datetime.tzinfo`, optional
        timezone of recorded data, either as string or as tzinfo object.
        Default: 'Europe/Berlin'
    split_into_nights : bool, optional
        whether to split the dataframe into the different recording nights (and return a dictionary of dataframes)
        or not.
        Default: ``True``

    Returns
    -------
    :class:`~pandas.DataFrame` or dict of such
        dataframe (or dict of dataframes, if ``split_into_nights`` is ``True``) with Sleep Analyzer data

    Raises
    ------
    ValueError
        if unsupported data source was passed
    `~biopsykit.utils.exceptions.FileExtensionError`
        if ``file_path`` is not a csv file
    `~biopsykit.utils.exceptions.ValidationError`
        if file does not have the required columns ``start``, ``duration``, ``value``

    """
    if data_source not in WITHINGS_RAW_DATA_SOURCES.values():
        raise ValueError(
            "Unsupported data source {}! Must be one of {}.".format(
                data_source, list(WITHINGS_RAW_DATA_SOURCES.values())
            )
        )

    if type(file) == bytes:
        file_path = Path(file_name)
    else:
        file_path = Path(file)
        file = file_path

    file_path = Path(file_path)
    _assert_file_extension(file_path, ".csv")

    data = _load_dataframe(file, file_name)

    _assert_has_columns(data, [["start", "duration", "value"]])

    if timezone is None:
        timezone = tz

    # convert string timestamps to datetime
    data["start"] = pd.to_datetime(data["start"])
    # sort index
    data = data.set_index("start").sort_index()
    # drop duplicate index values
    data = data.loc[~data.index.duplicated()]

    # convert it into the right time zone
    data = data.groupby("start", group_keys=False).apply(
        _localize_time, timezone=timezone
    )
    # convert strings of arrays to arrays
    data["duration"] = data["duration"].apply(literal_eval)
    data["value"] = data["value"].apply(literal_eval)

    # rename index
    data.index.name = "time"
    # explode data and apply timestamp explosion to groups
    data_explode = data.apply(pd.Series.explode)
    data_explode = data_explode.groupby("time", group_keys=False).apply(
        _explode_timestamp
    )
    # rename the value column
    data_explode.columns = [data_source]
    # convert dtypes from object into numerical values
    data_explode = data_explode.astype(int)
    # drop duplicate index values
    data_explode = data_explode.loc[~data_explode.index.duplicated()]

    if split_into_nights:
        data_explode = split_nights(data_explode)
        data_explode = {
            key: _reindex_datetime_index(d) for key, d in data_explode.items()
        }
    else:
        data_explode = _reindex_datetime_index(data_explode)
    return data_explode
