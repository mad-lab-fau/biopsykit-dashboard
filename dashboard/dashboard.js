importScripts("https://cdn.jsdelivr.net/pyodide/v0.23.4/pyc/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/1.2.3/dist/wheels/bokeh-3.2.2-py3-none-any.whl', 'https://cdn.holoviz.org/panel/1.2.3/dist/wheels/panel-1.2.3-py3-none-any.whl', 'pyodide-http==0.2.1', 'https://raw.githubusercontent.com/shMeske/WheelFiles/master/docopt-0.6.2-py2.py3-none-any.whl', 'https://raw.githubusercontent.com/shMeske/WheelFiles/master/littleutils-0.2.2-py3-none-any.whl', 'fau_colors==1.5.3','https://raw.githubusercontent.com/shMeske/WheelFiles/master/pingouin-0.5.4-py3-none-any.whl', 'biopsykit','seaborn', 'matplotlib', 'nilspodlib', 'numpy', 'packaging', 'pandas', 'param', 'plotly', 'pytz',  'typing_extensions','holoviews']

  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

import os
import warnings
import numpy as np
import pandas as pd
import nilspodlib
import panel as pn
import param
import datetime as datetime
import biopsykit as bp
import io
import itertools
import matplotlib.figure
import pytz
import zipfile
import seaborn as sns
import fau_colors
import re
import string
import math
import plotly.express as px
import matplotlib.pyplot as plt
os.environ["OUTDATED_IGNORE"] = "1"
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

from nilspodlib import Dataset
from nilspodlib.utils import path_t
from typing_extensions import Literal

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from nilspodlib import SyncedSession
from nilspodlib.dataset import split_into_sensor_data, Dataset
from nilspodlib.exceptions import LegacyWarning
from nilspodlib.header import Header
from nilspodlib.utils import path_t
from typing import Dict, Optional, Tuple, Iterable
from nilspodlib.legacy import find_conversion_function, legacy_support_check
from nilspodlib.utils import read_binary_uint8, get_strict_version_from_header_bytes
from packaging.version import Version
from typing_extensions import Self


def get_header_and_data_bytes(bin_file: BytesIO) -> Tuple[np.ndarray, np.ndarray]:
    """Separate a binary file into its header and data part."""
    header_size = np.frombuffer(bin_file.read(1), dtype=np.dtype("B"))
    header = np.append(
        header_size,
        np.frombuffer(bin_file.read(header_size[0] - 1), dtype=np.dtype("B")),
    )
    data_bytes = np.frombuffer(bin_file.read(), dtype=np.dtype("B"))
    return header, data_bytes


def parse_binary(
    bin_file: BytesIO,
    legacy_support: str = "error",
    force_version: Optional[Version] = None,
    tz: Optional[str] = None,
) -> Tuple[Dict[str, np.ndarray], np.ndarray, Header]:
    header_bytes, data_bytes = get_header_and_data_bytes(bin_file)
    version = get_strict_version_from_header_bytes(header_bytes)
    if legacy_support == "resolve":
        version = force_version or version
        header_bytes, data_bytes = find_conversion_function(version, in_memory=True)(
            header_bytes, data_bytes
        )
    elif legacy_support in ["error", "warn"]:
        legacy_support_check(version, as_warning=(legacy_support == "warn"))
    else:
        raise ValueError("legacy_support must be one of 'resolve', 'error' or 'warn'")

    session_header = Header.from_bin_array(header_bytes[1:], tz=tz)

    sample_size = session_header.sample_size
    n_samples = session_header.n_samples

    data = read_binary_uint8(data_bytes, sample_size, n_samples)

    counter, sensor_data = split_into_sensor_data(data, session_header)

    if (
        session_header.strict_version_firmware >= Version("0.13.0")
        and len(counter) != session_header.n_samples
    ):
        warnings.warn(
            "The number of samples in the dataset does not match the number indicated by the header. "
            "This might indicate a corrupted file",
            LegacyWarning,
        )

    return sensor_data, counter, session_header


class NilsPodAdapted(nilspodlib.Dataset):
    def __init__(
        self, sensor_data: Dict[str, np.ndarray], counter: np.ndarray, info: Header
    ):
        super().__init__(sensor_data, counter, info)

    @classmethod
    def from_bin_file(
        cls,
        filepath_or_buffer: path_t | BytesIO,
        *,
        legacy_support: str = "error",
        force_version: Optional[Version] = None,
        tz: Optional[str] = None,
    ) -> Self:
        if isinstance(filepath_or_buffer, BytesIO):
            sensor_data, counter, info = parse_binary(
                bin_file=filepath_or_buffer,
                legacy_support=legacy_support,
                force_version=force_version,
                tz=tz,
            )
            s = nilspodlib.Dataset(sensor_data, counter, info)
            return s
        else:
            path = Path(filepath_or_buffer)
            if path.suffix != ".bin":
                ValueError(
                    'Invalid file type! Only ".bin" files are supported not {}'.format(
                        path
                    )
                )

            sensor_data, counter, info = parse_binary(
                path, legacy_support=legacy_support, force_version=force_version, tz=tz
            )
            s = nilspodlib.Dataset(sensor_data, counter, info)

            s.path = path
            return s


class SyncedSessionAdapted(nilspodlib.SyncedSession):
    def __init__(self, datasets: Iterable[Dataset]):
        super().__init__(datasets)

    @classmethod
    def from_zip_file(
        cls,
        paths: Iterable[str],
        zip_file: ZipFile,
        legacy_support: str = "error",
        force_version: Version | None = None,
        tz: str | None = None,
    ) -> Self:
        ds = ()
        with zip_file as archive:
            for path in paths:
                ds += NilsPodAdapted.from_bin_file(
                    BytesIO(archive.read(path)),
                    legacy_support=legacy_support,
                    force_version=force_version,
                    tz=tz,
                )
        return SyncedSession(ds)

    @classmethod
    def from_folder_path(
        cls,
        zip_file: ZipFile,
        filter_pattern: str = "*.bin",
        legacy_support: str = "error",
        force_version: Optional[Version] = None,
        tz: Optional[str] = None,
    ) -> Self:
        ds = list(
            filter(lambda file: file.endswith(filter_pattern), zip_file.namelist())
        )  # hier müssen noch alle Dateien gesucht werden
        if not ds:
            raise ValueError(
                'No files matching "{}" where found in zipFile'.format(filter_pattern)
            )
        return SyncedSession(
            cls.from_zip_file(
                paths=ds,
                zip_file=zip_file,
                legacy_support=legacy_support,
                force_version=force_version,
                tz=tz,
            )
        )

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
                "using \`biopsykit.io.nilspod.load_synced_session_nilspod()\`. "
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

    It will return a \`SalivaRawDataFrame\`, a long-format dataframe that complies with BioPsyKit's naming convention,
    i.e., the subject ID index will be named \`\`subject\`\`, the sample index will be names \`\`sample\`\`,
    and the value column will be named after the saliva biomarker type.

    Parameters
    ----------
    file_path: :class:\`~pathlib.Path\` or str
        path to file
    saliva_type: str
        saliva type to load from file. Example: \`\`cortisol\`\`
    subject_col: str, optional
        name of column containing subject IDs or \`\`None\`\` to use the default column name \`\`subject\`\`.
        According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: \`\`None\`\`
    condition_col : str, optional
        name of the column containing condition assignments or \`\`None\`\` if no conditions are present.
        According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: \`\`None\`\`
    additional_index_cols : str or list of str, optional
        additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
        strings to indicate column name(s) that should be used as index level(s),
        or \`\`None\`\` for no additional index levels. Default: \`\`None\`\`
    sample_times: list of int, optional
        times at which saliva samples were collected or \`\`None\`\` if no sample times should be specified.
        Default: \`\`None\`\`
    **kwargs
        Additional parameters that are passed to :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`

    Returns
    -------
    data : :class:\`~biopsykit.utils.datatype_helper.SalivaRawDataFrame\`
        saliva data in \`SalivaRawDataFrame\` format

    Raises
    ------
    :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
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
    the subject ID index will be named \`\`subject\`\` and the condition column will be named \`\`condition\`\`.

    Parameters
    ----------
    file_path : :class:\`~pathlib.Path\` or str
        path to time log file. Must either be an Excel or csv file
    subject_col : str, optional
        name of column containing subject IDs or \`\`None\`\` to use default column name \`\`subject\`\`.
        According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    condition_col : str, optional
        name of column containing condition assignments or \`\`None\`\` to use default column name \`\`condition\`\`.
        According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    return_dict : bool, optional
        whether to return a dict with subject IDs per condition (\`\`True\`\`) or a dataframe (\`\`False\`\`).
        Default: \`\`False\`\`
    **kwargs
        Additional parameters that are passed tos :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`

    Returns
    -------
    :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame\` or
    :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDict\`
        a standardized pandas dataframe with subject IDs and condition assignments (if \`\`return_dict\`\` is \`\`False\`\`) or
        a standardized dict with subject IDs per group (if \`\`return_dict\`\` is \`\`True\`\`)

    Raises
    ------
    :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
        if file is not a csv or Excel file
    :exc:\`~biopsykit.utils.exceptions.ValidationError\`
        if result is not a :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame\` or a
        :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDict\`

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
#     It will return a \`SalivaRawDataFrame\`, a long-format dataframe that complies with BioPsyKit's naming convention,
#     i.e., the subject ID index will be named \`\`subject\`\`, the sample index will be names \`\`sample\`\`,
#     and the value column will be named after the saliva biomarker type.
#
#     Parameters
#     ----------
#     file_path: :class:\`~pathlib.Path\` or str
#         path to file
#     saliva_type: str
#         saliva type to load from file. Example: \`\`cortisol\`\`
#     subject_col: str, optional
#         name of column containing subject IDs or \`\`None\`\` to use the default column name \`\`subject\`\`.
#         According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
#         If the subject ID column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: \`\`None\`\`
#     condition_col : str, optional
#         name of the column containing condition assignments or \`\`None\`\` if no conditions are present.
#         According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
#         If the condition column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: \`\`None\`\`
#     additional_index_cols : str or list of str, optional
#         additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
#         strings to indicate column name(s) that should be used as index level(s),
#         or \`\`None\`\` for no additional index levels. Default: \`\`None\`\`
#     sample_times: list of int, optional
#         times at which saliva samples were collected or \`\`None\`\` if no sample times should be specified.
#         Default: \`\`None\`\`
#     **kwargs
#         Additional parameters that are passed to :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`
#
#     Returns
#     -------
#     data : :class:\`~biopsykit.utils.datatype_helper.SalivaRawDataFrame\`
#         saliva data in \`SalivaRawDataFrame\` format
#
#     Raises
#     ------
#     :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
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
    file : :class:\`~pathlib.Path\` or str
        path to file
    data_source : str
        data source of file specified by \`\`file_path\`\`. Must be one of
        ['heart_rate', 'respiration_rate', 'sleep_state', 'snoring'].
    timezone : str or :class:\`datetime.tzinfo\`, optional
        timezone of recorded data, either as string or as tzinfo object.
        Default: 'Europe/Berlin'
    split_into_nights : bool, optional
        whether to split the dataframe into the different recording nights (and return a dictionary of dataframes)
        or not.
        Default: \`\`True\`\`

    Returns
    -------
    :class:\`~pandas.DataFrame\` or dict of such
        dataframe (or dict of dataframes, if \`\`split_into_nights\`\` is \`\`True\`\`) with Sleep Analyzer data

    Raises
    ------
    ValueError
        if unsupported data source was passed
    \`~biopsykit.utils.exceptions.FileExtensionError\`
        if \`\`file_path\`\` is not a csv file
    \`~biopsykit.utils.exceptions.ValidationError\`
        if file does not have the required columns \`\`start\`\`, \`\`duration\`\`, \`\`value\`\`

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






def add_keys_nested_dict(d, keys):
    if d is None:
        d = {}
    if len(keys) == 1 and keys[0] not in d:
        d.setdefault(keys[0], None)
    else:
        key = keys[0]
        if key not in d:
            d[key] = {}
        if d[key] is None:
            d[key] = {}
        add_keys_nested_dict(d[key], keys[1:])


def change_value_nested_dict(d, keys, value):
    if len(keys) == 1:
        d[keys[0]] = value
    else:
        change_value_nested_dict(d[keys[0]], keys[1:], value)


# TODO: Rename Phase
class SetUpStudyDesign(param.Parameterized):
    add_study_btn = pn.widgets.Button(
        name="Add Study Part", button_type="primary", align="end"
    )
    study_name_input = pn.widgets.TextInput(
        name="Study Name",
        value="",
        placeholder="Type in here the name of the Study Part",
    )
    add_phase_btn = pn.widgets.Button(name="Add Phase", button_type="primary")
    add_subphase_btn = pn.widgets.Button(name="Add Subphase", button_type="primary")
    structure_accordion = pn.layout.Accordion(name="Study Structure")
    subject_time_dict = param.Dynamic()
    structure = {}

    def add_study_part(self, _):
        part_name = self.study_name_input.value
        if not self._assert_study_part_name(part_name):
            return
        self.structure[part_name] = None
        self.structure_accordion.append(self.get_phase_panel(part_name))

    def _assert_study_part_name(self, name):
        if name in self.structure.keys():
            pn.state.notifications.error("Study Part already exists")
            return False
        if name == "":
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        if name is None:
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        return True

    def state_add_phase(self, target, event):
        target.disabled = not self._assert_study_part_name(event.new)

    def state_add_value(self, target, event):
        target.disabled = event.new is None or event.new == ""

    # TODO
    def change_value(self, input_value, keys):
        change_value_nested_dict(self.structure, keys, input_value)

    # TODO: entsprechenden key aus Liste nehmen
    def remove_value(self, btn, keys):
        if not btn:
            return
        if len(keys) == 1:
            self.structure[keys[0]] = None
            index = self.get_accordion_index(keys[0])
            if index == -1:
                return
            self.structure_accordion.__setitem__(index, self.get_phase_panel(keys[0]))

    def add_value(self, input_value, btn, part_name, phase_row):
        if not btn:
            pn.state.notifications.warning("Click on Add Value in order to add a value")
            return
        change_value_nested_dict(self.structure, part_name, input_value)
        pn.state.notifications.success("Value added")
        phase_row.visible = False
        print(self.structure)
        # TODO: noch an richtige Stelle einfügen
        # self.structure_accordion.__setitem__(index, col)

    def get_accordion_index(self, name):
        index_list = [
            lst_index
            for (lst_index, element) in enumerate(self.structure_accordion.objects)
            if element.name == name
        ]
        if len(index_list) != 1:
            pn.state.notifications.error("Phase not found")
            return -1
        index = index_list[0]
        return index

    # TODO: Fix
    def remove_phase(self, btn, part_name, phase_name):
        if not btn:
            return
        pass
        # self.structure.pop(part_name)
        # index = self.get_accordion_index(part_name)
        # if index == -1:
        #     return
        # self.structure_accordion.pop(index)

    def add_subphase(
        self, btn, subphase_name_input, part_name, value_row, subphase_acc
    ):
        if not btn:
            return
        if not subphase_name_input:
            return
        value_row.visible = False
        key_list = part_name + [subphase_name_input]
        panel = self.get_phase_panel(key_list)
        subphase_acc.append(panel)
        add_keys_nested_dict(self.structure, key_list)

    def get_phase_panel(self, part_name) -> pn.Column:
        if not isinstance(part_name, list):
            part_name = [part_name]
        value_input = pn.widgets.IntInput(
            name="Value",
            placeholder="Type in here the value of the Phase",
        )
        value_add_btn = pn.widgets.Button(
            name="Add Value", button_type="primary", align="end", disabled=True
        )
        value_input.link(value_add_btn, callbacks={"value": self.state_add_value})
        subphase_name_input = pn.widgets.TextInput(
            name="Subphase Name",
            value="",
            placeholder="Type in here the name of the Subphase",
        )
        subphase_add_btn = pn.widgets.Button(
            name="Add Subphase", button_type="primary", align="end", disabled=False
        )
        if len(part_name) == 3:
            subphase_add_btn.visible = False
            subphase_name_input.visible = False
        value_row = pn.Row(value_input, value_add_btn)
        phase_row = pn.Row(subphase_name_input, subphase_add_btn)
        rename_input = pn.widgets.TextInput(
            name="Rename Phase", placeholder="Rename the Phase"
        )
        rename_btn = pn.widgets.Button(
            name="Rename", button_type="warning", align="end"
        )
        remove_phase_btn = pn.widgets.Button(
            name="Remove Phase", button_type="danger", align="end"
        )
        subphase_accordion = pn.layout.Accordion()
        pn.bind(
            self.remove_phase, remove_phase_btn, part_name, part_name[-1], watch=True
        )
        pn.bind(
            self.rename_phase,
            rename_btn,
            rename_input,
            part_name[-1],
            part_name,
            watch=True,
        )
        pn.bind(
            self.add_subphase,
            subphase_add_btn,
            subphase_name_input,
            part_name,
            value_row,
            subphase_accordion,
            watch=True,
        )
        col = pn.Column(
            value_row,
            phase_row,
            subphase_accordion,
            pn.layout.Divider(),
            remove_phase_btn,
            name=part_name[-1],
        )
        pn.bind(
            self.add_value, value_input, value_add_btn, part_name, phase_row, watch=True
        )
        return col

    def panel(self):
        self.add_study_btn.disabled = True
        self.study_name_input.link(
            self.add_study_btn, callbacks={"value_input": self.state_add_phase}
        )
        self.add_study_btn.on_click(self.add_study_part)
        text = "# Set up the study design \\n Here you can set up the study design. You can add study parts, phases and subphases."
        return pn.Column(
            pn.pane.Markdown(text),
            self.structure_accordion,
            pn.Row(self.study_name_input, self.add_study_btn),
        )





def add_keys_nested_dict(d, keys):
    if d is None:
        d = {}
    if len(keys) == 1 and keys[0] not in d:
        d.setdefault(keys[0], None)
    else:
        key = keys[0]
        if key not in d:
            d[key] = {}
        if d[key] is None:
            d[key] = {}
        add_keys_nested_dict(d[key], keys[1:])


def change_value_nested_dict(d, keys, value):
    if len(keys) == 1:
        d[keys[0]] = value
    else:
        change_value_nested_dict(d[keys[0]], keys[1:], value)


# TODO: Rename Phase
class SetUpStudyDesign(param.Parameterized):
    add_study_btn = pn.widgets.Button(
        name="Add Study Part", button_type="primary", align="end"
    )
    study_name_input = pn.widgets.TextInput(
        name="Study Name",
        value="",
        placeholder="Type in here the name of the Study Part",
    )
    add_phase_btn = pn.widgets.Button(name="Add Phase", button_type="primary")
    add_subphase_btn = pn.widgets.Button(name="Add Subphase", button_type="primary")
    structure_accordion = pn.layout.Accordion(name="Study Structure")
    subject_time_dict = param.Dynamic()
    structure = {}

    def add_study_part(self, _):
        part_name = self.study_name_input.value
        if not self._assert_study_part_name(part_name):
            return
        self.structure[part_name] = None
        self.structure_accordion.append(self.get_phase_panel(part_name))

    def _assert_study_part_name(self, name):
        if name in self.structure.keys():
            pn.state.notifications.error("Study Part already exists")
            return False
        if name == "":
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        if name is None:
            pn.state.notifications.warning("Please enter a name for the study part")
            return False
        return True

    def state_add_phase(self, target, event):
        target.disabled = not self._assert_study_part_name(event.new)

    def state_add_value(self, target, event):
        target.disabled = event.new is None or event.new == ""

    # TODO
    def change_value(self, input_value, keys):
        change_value_nested_dict(self.structure, keys, input_value)

    # TODO: entsprechenden key aus Liste nehmen
    def remove_value(self, btn, keys):
        if not btn:
            return
        if len(keys) == 1:
            self.structure[keys[0]] = None
            index = self.get_accordion_index(keys[0])
            if index == -1:
                return
            self.structure_accordion.__setitem__(index, self.get_phase_panel(keys[0]))

    def add_value(self, input_value, btn, part_name, phase_row):
        if not btn:
            pn.state.notifications.warning("Click on Add Value in order to add a value")
            return
        change_value_nested_dict(self.structure, part_name, input_value)
        pn.state.notifications.success("Value added")
        phase_row.visible = False
        print(self.structure)
        # TODO: noch an richtige Stelle einfügen
        # self.structure_accordion.__setitem__(index, col)

    def get_accordion_index(self, name):
        index_list = [
            lst_index
            for (lst_index, element) in enumerate(self.structure_accordion.objects)
            if element.name == name
        ]
        if len(index_list) != 1:
            pn.state.notifications.error("Phase not found")
            return -1
        index = index_list[0]
        return index

    # TODO: Fix
    def remove_phase(self, btn, part_name, phase_name):
        if not btn:
            return
        pass
        # self.structure.pop(part_name)
        # index = self.get_accordion_index(part_name)
        # if index == -1:
        #     return
        # self.structure_accordion.pop(index)

    def add_subphase(
        self, btn, subphase_name_input, part_name, value_row, subphase_acc
    ):
        if not btn:
            return
        if not subphase_name_input:
            return
        value_row.visible = False
        key_list = part_name + [subphase_name_input]
        panel = self.get_phase_panel(key_list)
        subphase_acc.append(panel)
        add_keys_nested_dict(self.structure, key_list)

    def get_phase_panel(self, part_name) -> pn.Column:
        if not isinstance(part_name, list):
            part_name = [part_name]
        value_input = pn.widgets.IntInput(
            name="Value",
            placeholder="Type in here the value of the Phase",
        )
        value_add_btn = pn.widgets.Button(
            name="Add Value", button_type="primary", align="end", disabled=True
        )
        value_input.link(value_add_btn, callbacks={"value": self.state_add_value})
        subphase_name_input = pn.widgets.TextInput(
            name="Subphase Name",
            value="",
            placeholder="Type in here the name of the Subphase",
        )
        subphase_add_btn = pn.widgets.Button(
            name="Add Subphase", button_type="primary", align="end", disabled=False
        )
        if len(part_name) == 3:
            subphase_add_btn.visible = False
            subphase_name_input.visible = False
        value_row = pn.Row(value_input, value_add_btn)
        phase_row = pn.Row(subphase_name_input, subphase_add_btn)
        rename_input = pn.widgets.TextInput(
            name="Rename Phase", placeholder="Rename the Phase"
        )
        rename_btn = pn.widgets.Button(
            name="Rename", button_type="warning", align="end"
        )
        remove_phase_btn = pn.widgets.Button(
            name="Remove Phase", button_type="danger", align="end"
        )
        subphase_accordion = pn.layout.Accordion()
        pn.bind(
            self.remove_phase, remove_phase_btn, part_name, part_name[-1], watch=True
        )
        pn.bind(
            self.rename_phase,
            rename_btn,
            rename_input,
            part_name[-1],
            part_name,
            watch=True,
        )
        pn.bind(
            self.add_subphase,
            subphase_add_btn,
            subphase_name_input,
            part_name,
            value_row,
            subphase_accordion,
            watch=True,
        )
        col = pn.Column(
            value_row,
            phase_row,
            subphase_accordion,
            pn.layout.Divider(),
            remove_phase_btn,
            name=part_name[-1],
        )
        pn.bind(
            self.add_value, value_input, value_add_btn, part_name, phase_row, watch=True
        )
        return col

    def panel(self):
        self.add_study_btn.disabled = True
        self.study_name_input.link(
            self.add_study_btn, callbacks={"value_input": self.state_add_phase}
        )
        self.add_study_btn.on_click(self.add_study_part)
        text = "# Set up the study design \\n Here you can set up the study design. You can add study parts, phases and subphases."
        return pn.Column(
            pn.pane.Markdown(text),
            self.structure_accordion,
            pn.Row(self.study_name_input, self.add_study_btn),
        )

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class PsychologicalPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(
            debug=True,
        )

        # self.pipeline.add_stage("Test", TestPage(), ready_parameter="ready")
        self.pipeline.add_stage("Set upt Study Design", SetUpStudyDesign())

        # self.pipeline.add_stage(
        #     "Ask for Subject Condition List",
        #     AskToLoadConditionList(),
        #     ready_parameter="ready",
        #     next_parameter="next_page",
        #     auto_advance=True,
        # )

        # self.pipeline.define_graph(
        #     {
        #         "Ask for Recording Device": "Set Parsing Parameters",
        #         "Set Parsing Parameters": "Ask for Format",
        #         "Ask for Format": "Upload Sleep Data",
        #     }
        # )




class SetSampleTimes(param.Parameterized):
    data = param.Dynamic(default=None)
    saliva_type = param.String(default=None)
    sample_times = param.Dynamic(default=None)
    sample_times_input = pn.widgets.ArrayInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
    )
    ready = param.Boolean(default=False)

    def sample_times_changed(self, event):
        self.sample_times = event.new
        if self.sample_times is None or len(self.sample_times) == 0:
            self.ready = False
        else:
            self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.saliva_type,
            self.sample_times,
        )

    def panel(self):
        self.sample_times_input.param.watch(self.sample_times_changed, "value")
        return pn.Column(
            pn.pane.Markdown("# Enter the sample times"),
            self.sample_times_input,
        )


SALIVA_MAX_STEPS = 4

ASK_FOR_FORMAT_TEXT = "# Choose the format your data is stored in"
ASK_TO_LOAD_CONDITION_LIST_TEXT = "# Do you want to add a condition list?"
ADD_CONDITION_LIST_TEXT = "# Add a condition list"
LOAD_PLATE_DATA_TEXT = (
    "# Upload Saliva Data \\n Here you can upload the saliva data. "
    "In the following steps you can analyze the data and then download the results."
)
SHOW_FEATURES_TEXT = "# Show Features"





SALIVA_MAX_STEPS = 4

ASK_FOR_FORMAT_TEXT = "# Choose the format your data is stored in"
ASK_TO_LOAD_CONDITION_LIST_TEXT = "# Do you want to add a condition list?"
ADD_CONDITION_LIST_TEXT = "# Add a condition list"
LOAD_PLATE_DATA_TEXT = (
    "# Upload Saliva Data \\n Here you can upload the saliva data. "
    "In the following steps you can analyze the data and then download the results."
)
SHOW_FEATURES_TEXT = "# Show Features"

from typing import Dict, List

from biopsykit.signals._base import _BaseProcessor


class PipelineHeader(pn.viewable.Viewer):
    max_step = param.Integer(default=100)

    def __init__(
        self,
        step: int | param.Integer,
        max_step: int | param.Integer,
        text: str | param.String,
        **params,
    ):
        self.max_step = max_step
        self._progress = pn.indicators.Progress(
            name="Progress",
            height=20,
            sizing_mode="stretch_width",
            max=max_step,
            value=step,
        )
        self._step_text = pn.widgets.StaticText(
            name="Progress", value="Step " + str(step) + " of " + str(max_step)
        )
        self.text = pn.pane.Markdown(text)
        super().__init__(**params)
        self._layout = pn.Column(
            pn.Row(self._step_text),
            pn.Row(self._progress),
            pn.Column(self.text),
        )

    def update_step(self, step: int):
        self._step_text.value = "Step " + str(step) + " of " + str(self.max_step)
        self._progress.value = step

    def update_text(self, text: str):
        self.text = pn.pane.Markdown(text)

    def __panel__(self):
        return self._layout


class Timestamp(pn.viewable.Viewer):

    value = param.Tuple(doc="First value is the name the second the timestamp")
    remove = False
    name = param.String()

    def __init__(self, **params):
        self._timestamp_name = pn.widgets.StaticText()
        self._timestamp_datetime = pn.widgets.DatetimePicker()
        self._timestamp_remove = pn.widgets.Button(name="Remove", button_type="primary")
        super().__init__(**params)
        self._layout = pn.Row(
            self._timestamp_name, self._timestamp_datetime, self._timestamp_remove
        )
        self._sync_widgets()
        # self._timestamp_remove.on_click(self.)

    def __panel__(self):
        return self._layout

    @param.depends("_timestamp_remove.value", watch=True)
    def remove_btn_click(self):
        self.remove = True

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        self._timestamp_name.value = self.value[0]
        self._timestamp_datetime.value = self.value[1]

    @param.depends("_timestamp_datetime.value", watch=True)
    def _sync_params(self):
        self.value = (self._timestamp_name.value, self._timestamp_datetime.value)


class TimestampList(pn.viewable.Viewer):

    value = param.List(doc="List of Tuples (str, DateTime)")
    col = pn.Column()
    timestamps = []
    name = param.String()

    def __init__(self, **params):
        super().__init__(**params)
        self._layout = self.col
        self._sync_widgets()

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        for nt in self.value:
            ts = Timestamp(name=nt[0], value=(nt[0], nt[1]))
            ts._timestamp_remove.on_click(self.remove_btn_click)
            self.col.append(ts)

    def __panel__(self):
        self._layout = self.col
        return self._layout

    def remove_btn_click(self, event):
        # Check all Items in
        print("In TimestampList")
        print(event)


class SubjectDataFrameView(pn.viewable.Viewer):
    def __init__(
        self, subjects: Dict[str, Dict[str, Dict[str, pd.DataFrame]]], **params
    ):
        self._subject_results_dict = subjects
        self.select_subject = pn.widgets.Select(name="Subject")
        if subjects is not None and len(subjects.keys()) > 0:
            self.select_subject.options = list(subjects.keys())
        self.select_subject.link(self, callbacks={"value": self.change_subject})
        self.select_result = pn.widgets.Select(name="Result", options=["init"])
        self.select_result.link(self, callbacks={"value": self.change_result})
        self.select_phase = pn.widgets.Select(name="Phase", options=[])
        self.select_phase.link(self, callbacks={"value": self.change_phase})
        self.tab = pn.widgets.Tabulator(
            name="Results",
            pagination="local",
            layout="fit_data_stretch",
            page_size=15,
            visible=False,
        )
        self._layout = pn.Column(
            pn.Row(self.select_subject, self.select_result, self.select_phase),
            self.tab,
        )
        super().__init__(**params)

    def set_subject_results(
        self, subjects: Dict[str, Dict[str, Dict[str, pd.DataFrame]]]
    ):
        self._subject_results_dict = subjects
        self.select_subject.options = list(subjects.keys())

    def change_subject(self, target, event):
        self.select_result.options = list(self._subject_results_dict[event.new].keys())
        subject = event.new
        result = self.select_result.value
        phase = self.select_phase.value
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def change_result(self, target, event):
        subject = self.select_subject.value
        result = event.new
        self.select_phase.options = list(
            self._subject_results_dict[subject][result].keys()
        )
        phase = self.select_phase.value
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def change_phase(self, target, event):
        subject = self.select_subject.value
        result = self.select_result.value
        phase = event.new
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def __panel__(self):
        return self._layout


class PlotViewer(pn.viewable.Viewer):
    def __init__(
        self,
        signal_type: str | None,
        signal: Dict[str, _BaseProcessor] | None,
        sampling_rate: float | None,
        **params,
    ):
        self._signal_type = signal_type
        self._signal = signal
        self._sampling_rate = sampling_rate
        self.select_result = pn.widgets.Select(name="Result")
        self.select_phase = pn.widgets.Select(name="Phase")
        if signal is not None:
            self.select_result.options = list(signal.keys())
        self.graph = pn.pane.Matplotlib()
        self.select_result.link(self.graph, callbacks={"value": self.change_result})
        self.select_phase.link(self.graph, callbacks={"value": self.change_phase})
        self._layout = pn.Column(
            pn.Row(self.select_result, self.select_phase), self.graph
        )
        super().__init__(**params)

    def set_signal_type(self, signal_type: str):
        self._signal_type = signal_type

    def set_sampling_rate(self, sampling_rate: float):
        self._sampling_rate = sampling_rate

    def set_values(
        self, signal_type: str, signal: Dict[str, _BaseProcessor], sampling_rate: float
    ):
        self._signal_type = signal_type
        self._signal = signal
        self._sampling_rate = sampling_rate
        self.select_result.options = list(signal.keys())

    def set_signal(self, signal: Dict[str, pd.DataFrame]):
        self._signal = signal
        self.select_result.options = list(signal.keys())

    def change_phase(self, target, event):
        phase = event.new
        subject = self.select_result.value
        if subject is None or phase is None:
            return
        if self._signal_type == "ECG" and self._signal is not None:
            self.select_phase.options = list()
            fig, _ = bp.signals.ecg.plotting.ecg_plot(
                ecg_processor=self._signal[subject],
                sampling_rate=self._sampling_rate,
                key=phase,
            )
            target.object = fig

    def change_result(self, target, event):
        if self._signal_type == "ECG" and self._signal is not None:
            self.select_phase.options = list()
            fig, _ = bp.signals.ecg.plotting.ecg_plot(
                ecg_processor=self._signal[event.new],
                sampling_rate=self._sampling_rate,
                key=self._signal[event.new].phases[0],
            )
            self.select_phase.options = self._signal[event.new].phases
            target.object = fig

    def __panel__(self):
        return self._layout


class TimesToSubject(pn.viewable.Viewer):

    accordion = pn.Accordion()
    subject_time_dict = param.Dict(default={})
    add_new_subject_selector = pn.widgets.Select(
        name="Add New Subject", align=("start", "end")
    )
    add_new_subject_btn = pn.widgets.Button(
        name="Add New Subject", button_type="primary", align=("start", "end")
    )
    files_to_subjects = {}
    ready = not any(files_to_subjects.values()) is None

    def __init__(self, subject_names: List[str], **params):
        super().__init__(**params)
        self.add_new_subject_selector.options = subject_names
        for subject in subject_names:
            self.files_to_subjects[subject] = None
        self.add_new_subject_btn.link(
            self.add_new_subject_selector, callbacks={"clicks": self.add_new_subject}
        )
        self._layout = pn.Column(
            self.accordion,
            pn.Row(self.add_new_subject_selector, self.add_new_subject_btn),
        )

    def initialize_filenames(self, filenames: List[str]):
        self.add_new_subject_selector.options = filenames
        for subject in filenames:
            self.files_to_subjects[subject] = None
        self.add_new_subject_btn.link(
            self.add_new_subject_selector, callbacks={"clicks": self.add_new_subject}
        )

    def assign_file_to_subject(self, target, _):
        new_subject = target[0]
        file_name = target[1].value
        self.files_to_subjects[file_name] = new_subject
        if file_name == "":
            pn.state.notifications.warning(
                f"Please assign a file to the subject {new_subject}"
            )
        else:
            pn.state.notifications.success(
                f"Successfully assigned file {file_name} to subject {new_subject}"
            )

    def add_new_subject_time_dict(
        self, new_subject_time_dict: Dict[str, Dict[str, pd.DataFrame]]
    ):
        for subject in new_subject_time_dict.keys():
            self.append_subject_to_accordion(subject, new_subject_time_dict[subject])

    def add_new_subject(self, target, _):
        if (
            target.value is None
            or target.value == ""
            or target.value in self.subject_time_dict.keys()
        ):
            pn.state.notifications.error("Subject already added")
            return
        self.files_to_subjects[target.value] = target.value
        self.append_subject_to_accordion(target.value)

    def append_subject_to_accordion(
        self, subject_name: str, time_dict: None | Dict[str, pd.DataFrame] = None
    ):
        if subject_name in self.subject_time_dict.keys():
            return
        self.subject_time_dict[subject_name] = time_dict
        self.accordion.append(self.get_subject_column(subject_name))

    def get_subject_column(self, subject_name: str) -> pn.Column:
        col = pn.Column(name=subject_name)
        rename_input = pn.widgets.TextInput(
            name=f"Rename Subject {subject_name}:", align=("start", "end")
        )
        new_phase_input = pn.widgets.TextInput(
            name="New Phase Name:", align=("start", "end")
        )
        add_phase_btn = pn.widgets.Button(
            name="Add Phase", button_type="primary", align=("start", "end")
        )
        add_phase_btn.link(
            (
                subject_name,
                new_phase_input,
                col,
            ),
            callbacks={"clicks": self.add_phase_to_subject},
        )
        remove_btn = pn.widgets.Button(
            name=f"Remove {subject_name}", button_type="danger", align=("start", "end")
        )
        if self.subject_time_dict[subject_name] is not None:
            associate_file_to_subject_selector = pn.widgets.Select(
                name="Subject",
                options=[""] + list(self.files_to_subjects.keys()),
                align=("start", "end"),
            )
            associate_file_to_subject_btn = pn.widgets.Button(
                name="Associate", button_type="primary", align=("start", "end")
            )
            associate_file_to_subject_btn.link(
                (
                    subject_name,
                    associate_file_to_subject_selector,
                ),
                callbacks={"clicks": self.assign_file_to_subject},
            )
            col.append(
                pn.Row(
                    associate_file_to_subject_selector,
                    associate_file_to_subject_btn,
                )
            )
            col.append(pn.layout.Divider())
            for phase in self.subject_time_dict[subject_name]:
                phase_name_input = pn.widgets.TextInput(
                    placeholder=phase, value=phase, align=("start", "end")
                )
                phase_name_input.link(
                    (
                        subject_name,
                        col,
                    ),
                    callbacks={"value": self.rename_phase},
                )
                remove_phase_btn = pn.widgets.Button(
                    name=f"Remove {phase}", button_type="danger", align=("start", "end")
                )
                remove_phase_btn.link(
                    (
                        subject_name,
                        phase,
                        col,
                    ),
                    callbacks={"clicks": self.remove_phase},
                )
                col.append(pn.Row(phase_name_input, remove_phase_btn))
                for subphase, time in (
                    self.subject_time_dict[subject_name][phase].items()
                    if self.subject_time_dict[subject_name][phase] is not None
                    else []
                ):
                    subphase_name_input = pn.widgets.TextInput(
                        value=subphase, align=("start", "end")
                    )
                    subphase_dt_picker = pn.widgets.DatetimePicker(
                        value=time, align=("start", "end")
                    )
                    subphase_remove_btn = pn.widgets.Button(
                        name="Remove", button_type="danger", align=("start", "end")
                    )
                    subphase_remove_btn.link(
                        (
                            subject_name,
                            phase,
                            subphase,
                            col,
                        ),
                        callbacks={"clicks": self.remove_subphase},
                    )
                    col.append(
                        pn.Row(
                            subphase_name_input,
                            subphase_dt_picker,
                            subphase_remove_btn,
                        )
                    )
                add_subphase_btn = pn.widgets.Button(
                    name="Add Subphase", button_type="primary"
                )
                add_subphase_btn.link(
                    (subject_name, phase, col),
                    callbacks={"clicks": self.add_subphase_btn_click},
                )
                col.append(pn.Row(pn.layout.HSpacer(), add_subphase_btn))
        col.append(pn.Row(new_phase_input, add_phase_btn))
        col.append(pn.layout.Divider())
        col.append(rename_input)
        col.append(remove_btn)
        rename_input.link(col, callbacks={"value": self.rename_subject})
        remove_btn.link(col, callbacks={"clicks": self.remove_subject})
        return col

    def add_subphase_btn_click(self, target, _):
        subject_name = target[0]
        phase = target[1]
        subject_col = target[2]
        new_phase_name = "New Subphase"
        if (
            self.subject_time_dict[subject_name][phase] is None
            or len(self.subject_time_dict[subject_name][phase]) == 0
        ):
            self.subject_time_dict[subject_name][phase] = pd.Series(
                {new_phase_name: datetime.datetime.now()}
            )
        elif new_phase_name not in list(
            self.subject_time_dict[subject_name][phase].index.values
        ):
            self.subject_time_dict[subject_name][phase] = pd.concat(
                [
                    self.subject_time_dict[subject_name][phase],
                    pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
                ]
            )
        elif new_phase_name in list(
            self.subject_time_dict[subject_name][phase].index.values
        ):
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in list(
                self.subject_time_dict[subject_name][phase].index.values
            ):
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
            self.subject_time_dict[subject_name][phase] = pd.concat(
                [
                    self.subject_time_dict[subject_name][phase],
                    pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
                ]
            )
        index = self.accordion.objects.index(subject_col)
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def add_phase_to_subject(self, target, _):
        subject_name = target[0]
        new_phase_name = target[1].value
        if new_phase_name is None or new_phase_name == "":
            pn.state.notifications.error("Phase name must be filled out")
            return
        if (
            self.subject_time_dict[subject_name] is not None
            and new_phase_name in self.subject_time_dict[subject_name].keys()
        ):
            pn.state.notifications.error("Phase already added")
            return
        if self.subject_time_dict[subject_name] is None:
            self.subject_time_dict[subject_name] = {new_phase_name: None}
        else:
            self.subject_time_dict[subject_name][new_phase_name] = None
        index = self.accordion.objects.index(target[2])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def rename_phase(self, target, event):
        subject_name = target[0]
        new_phase_name = event.new
        old_phase_name = event.old
        self.subject_time_dict[subject_name][new_phase_name] = self.subject_time_dict[
            subject_name
        ].pop(old_phase_name)
        index = self.accordion.objects.index(target[1])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def rename_subject(self, target, event):
        file_name = self.get_filename_of_subject(target.name)
        self.files_to_subjects[file_name] = event.new
        index = self.accordion.objects.index(target)
        self.subject_time_dict[event.new] = self.subject_time_dict.pop(target.name)
        col = self.get_subject_column(event.new)
        self.accordion.__setitem__(index, col)

    def get_filename_of_subject(self, subject_name: str) -> str:
        for file_name, subject in self.files_to_subjects.items():
            if subject == subject_name:
                return file_name
        return ""

    def remove_subphase(self, target, _):
        subject_name = target[0]
        phase = target[1]
        subphase = target[2]
        old_col = target[3]
        self.subject_time_dict[subject_name][phase].pop(subphase)
        index = self.accordion.objects.index(old_col)
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def remove_phase(self, target, _):
        subject_name = target[0]
        phase = target[1]
        self.subject_time_dict[subject_name].pop(phase)
        index = self.accordion.objects.index(target[2])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def remove_subject(self, target, _):
        self.subject_time_dict.pop(target.name)
        self.accordion.remove(target)

    def get_subject_time_dict(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        return self.subject_time_dict

    def get_files_to_subjects(self) -> Dict[str, str]:
        return self.files_to_subjects

    def is_ready(self) -> bool:
        return not any(self.files_to_subjects.values()) is None

    def __panel__(self):
        return self._layout


class SalivaBase(param.Parameterized):
    condition_list = param.Dynamic(default=None)
    data = param.Dynamic()
    format = param.String(default=None)
    saliva_type = param.String(default="")
    sample_id = param.String(default=None)
    sample_times = param.Dynamic()
    step = param.Integer(default=1)

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, SALIVA_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    @param.output(
        ("condition_list", param.Dynamic),
        ("format", param.String),
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.List),
    )
    def output(self):
        return (
            self.condition_list,
            self.format,
            self.data,
            self.saliva_type,
            self.sample_times,
        )


class AskForFormat(SalivaBase):
    format_selector = pn.widgets.Select(
        options=["", "Wide Format", "Plate Format"],
        name="Format",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_FOR_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(ASK_FOR_FORMAT_TEXT)
        self.format_selector.link(self, callbacks={"value": self.format_changed})
        self._view = pn.Column(
            self.header,
            self.format_selector,
        )

    def format_changed(self, _, event):
        self.format = event.new
        self.ready = bool(event.new)

    def panel(self):
        return self._view

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

from nilspodlib import Dataset
from nilspodlib.utils import path_t
from typing_extensions import Literal


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
                "using \`biopsykit.io.nilspod.load_synced_session_nilspod()\`. "
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

    It will return a \`SalivaRawDataFrame\`, a long-format dataframe that complies with BioPsyKit's naming convention,
    i.e., the subject ID index will be named \`\`subject\`\`, the sample index will be names \`\`sample\`\`,
    and the value column will be named after the saliva biomarker type.

    Parameters
    ----------
    file_path: :class:\`~pathlib.Path\` or str
        path to file
    saliva_type: str
        saliva type to load from file. Example: \`\`cortisol\`\`
    subject_col: str, optional
        name of column containing subject IDs or \`\`None\`\` to use the default column name \`\`subject\`\`.
        According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: \`\`None\`\`
    condition_col : str, optional
        name of the column containing condition assignments or \`\`None\`\` if no conditions are present.
        According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function. Default: \`\`None\`\`
    additional_index_cols : str or list of str, optional
        additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
        strings to indicate column name(s) that should be used as index level(s),
        or \`\`None\`\` for no additional index levels. Default: \`\`None\`\`
    sample_times: list of int, optional
        times at which saliva samples were collected or \`\`None\`\` if no sample times should be specified.
        Default: \`\`None\`\`
    **kwargs
        Additional parameters that are passed to :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`

    Returns
    -------
    data : :class:\`~biopsykit.utils.datatype_helper.SalivaRawDataFrame\`
        saliva data in \`SalivaRawDataFrame\` format

    Raises
    ------
    :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
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
    the subject ID index will be named \`\`subject\`\` and the condition column will be named \`\`condition\`\`.

    Parameters
    ----------
    file_path : :class:\`~pathlib.Path\` or str
        path to time log file. Must either be an Excel or csv file
    subject_col : str, optional
        name of column containing subject IDs or \`\`None\`\` to use default column name \`\`subject\`\`.
        According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
        If the subject ID column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    condition_col : str, optional
        name of column containing condition assignments or \`\`None\`\` to use default column name \`\`condition\`\`.
        According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
        If the condition column in the file has another name, the column will be renamed in the dataframe
        returned by this function.
    return_dict : bool, optional
        whether to return a dict with subject IDs per condition (\`\`True\`\`) or a dataframe (\`\`False\`\`).
        Default: \`\`False\`\`
    **kwargs
        Additional parameters that are passed tos :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`

    Returns
    -------
    :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame\` or
    :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDict\`
        a standardized pandas dataframe with subject IDs and condition assignments (if \`\`return_dict\`\` is \`\`False\`\`) or
        a standardized dict with subject IDs per group (if \`\`return_dict\`\` is \`\`True\`\`)

    Raises
    ------
    :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
        if file is not a csv or Excel file
    :exc:\`~biopsykit.utils.exceptions.ValidationError\`
        if result is not a :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDataFrame\` or a
        :class:\`~biopsykit.utils.datatype_helper.SubjectConditionDict\`

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
#     It will return a \`SalivaRawDataFrame\`, a long-format dataframe that complies with BioPsyKit's naming convention,
#     i.e., the subject ID index will be named \`\`subject\`\`, the sample index will be names \`\`sample\`\`,
#     and the value column will be named after the saliva biomarker type.
#
#     Parameters
#     ----------
#     file_path: :class:\`~pathlib.Path\` or str
#         path to file
#     saliva_type: str
#         saliva type to load from file. Example: \`\`cortisol\`\`
#     subject_col: str, optional
#         name of column containing subject IDs or \`\`None\`\` to use the default column name \`\`subject\`\`.
#         According to BioPsyKit's convention, the subject ID column is expected to have the name \`\`subject\`\`.
#         If the subject ID column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: \`\`None\`\`
#     condition_col : str, optional
#         name of the column containing condition assignments or \`\`None\`\` if no conditions are present.
#         According to BioPsyKit's convention, the condition column is expected to have the name \`\`condition\`\`.
#         If the condition column in the file has another name, the column will be renamed in the dataframe
#         returned by this function. Default: \`\`None\`\`
#     additional_index_cols : str or list of str, optional
#         additional index levels to be added to the dataframe, e.g., "day" index. Can either be a string or a list
#         strings to indicate column name(s) that should be used as index level(s),
#         or \`\`None\`\` for no additional index levels. Default: \`\`None\`\`
#     sample_times: list of int, optional
#         times at which saliva samples were collected or \`\`None\`\` if no sample times should be specified.
#         Default: \`\`None\`\`
#     **kwargs
#         Additional parameters that are passed to :func:\`pandas.read_csv\` or :func:\`pandas.read_excel\`
#
#     Returns
#     -------
#     data : :class:\`~biopsykit.utils.datatype_helper.SalivaRawDataFrame\`
#         saliva data in \`SalivaRawDataFrame\` format
#
#     Raises
#     ------
#     :exc:\`~biopsykit.utils.exceptions.FileExtensionError\`
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
    file : :class:\`~pathlib.Path\` or str
        path to file
    data_source : str
        data source of file specified by \`\`file_path\`\`. Must be one of
        ['heart_rate', 'respiration_rate', 'sleep_state', 'snoring'].
    timezone : str or :class:\`datetime.tzinfo\`, optional
        timezone of recorded data, either as string or as tzinfo object.
        Default: 'Europe/Berlin'
    split_into_nights : bool, optional
        whether to split the dataframe into the different recording nights (and return a dictionary of dataframes)
        or not.
        Default: \`\`True\`\`

    Returns
    -------
    :class:\`~pandas.DataFrame\` or dict of such
        dataframe (or dict of dataframes, if \`\`split_into_nights\`\` is \`\`True\`\`) with Sleep Analyzer data

    Raises
    ------
    ValueError
        if unsupported data source was passed
    \`~biopsykit.utils.exceptions.FileExtensionError\`
        if \`\`file_path\`\` is not a csv file
    \`~biopsykit.utils.exceptions.ValidationError\`
        if file does not have the required columns \`\`start\`\`, \`\`duration\`\`, \`\`value\`\`

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


class AskToLoadConditionList(SalivaBase):
    no_condition_list_btn = pn.widgets.Button(name="No", button_type="primary")
    add_condition_list_btn = pn.widgets.Button(name="Yes")
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Add Condition List",
        objects=[
            "Add Condition List",
            "Load Saliva Data",
        ],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_LOAD_CONDITION_LIST_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(ASK_TO_LOAD_CONDITION_LIST_TEXT)
        self.no_condition_list_btn.link(
            self, callbacks={"clicks": self.no_condition_list}
        )
        self.add_condition_list_btn.link(
            self, callbacks={"clicks": self.add_condition_list}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.add_condition_list_btn, self.no_condition_list_btn),
        )

    def no_condition_list(self, _, event):
        self.next_page = "Load Saliva Data"
        self.ready = True

    def add_condition_list(self, _, event):
        self.next_page = "Add Condition List"
        self.ready = True

    def panel(self):
        return self._view


class AddConditionList(SalivaBase):
    ready = param.Boolean(default=False)
    upload_condition_list_btn = pn.widgets.FileInput(
        name="Upload condition list", accept=".csv,.xls,.xlsx", multiple=False
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ADD_CONDITION_LIST_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(ADD_CONDITION_LIST_TEXT)
        self.upload_condition_list_btn.link(
            self, callbacks={"value": self.parse_file_input}
        )
        self._view = pn.Column(
            self.header,
            self.upload_condition_list_btn,
        )

    def parse_file_input(self, target, event):
        try:
            self.condition_list = load_subject_condition_list(
                self.upload_condition_list_btn.value,
                self.upload_condition_list_btn.filename,
            )
            pn.state.notifications.success("Condition List successfully loaded")
            self.ready = True
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def panel(self):
        return self._view



class LoadSalivaData(SalivaBase):
    ready = param.Boolean(default=False)
    temporary_dataframe = param.DataFrame(default=None)
    upload_btn = pn.widgets.FileInput(accept=".csv,.xls,.xlsx", multiple=False)
    select_saliva = pn.widgets.Select(
        name="Choose the saliva type",
        options=["", "cortisol", "amylase"],
        visible=False,
    )
    select_subject_col = pn.widgets.Select(
        name="Select Subject Column", options=[], visible=False
    )
    select_condition_col = pn.widgets.Select(
        name="Select Condition Column", options=[], visible=False
    )
    select_additional_index_cols = pn.widgets.MultiChoice(
        name="Select Additional Index Columns",
        options=[],
        visible=False,
    )
    sample_times_input = pn.widgets.TextInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
        visible=False,
    )
    select_id_col_names = pn.widgets.MultiChoice(
        name="Select Id Columns",
        options=[],
        visible=False,
    )
    select_sample_id_col = pn.widgets.Select(
        name="Select Sample ID Column", options=[], visible=False
    )
    select_data_col = pn.widgets.Select(
        name="Select Data Column", options=[], visible=False
    )
    regex_input = pn.widgets.TextInput(
        name="Regex for sample id",
        value=None,
        placeholder="regular expression to extract subject ID, day ID and sample ID from the sample identifier",
        visible=False,
    )
    fill_condition_list = pn.widgets.Checkbox(name="Set Condition List", visible=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOAD_PLATE_DATA_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(LOAD_PLATE_DATA_TEXT)
        self.select_saliva.link(self, callbacks={"value": self.saliva_type_changed})
        self.upload_btn.link(self, callbacks={"value": self.parse_file_input})
        self._view = pn.Column(
            self.header,
            self.upload_btn,
            self.select_saliva,
            self.get_wide_format_column(),
            self.get_plate_format_column(),
        )

    def switch_plate_format_visibility(self, visible: bool):
        self.select_sample_id_col.visible = visible
        self.select_data_col.visible = visible
        self.select_id_col_names.visible = visible
        self.regex_input.visible = visible
        self.sample_times_input.visible = visible
        self.fill_condition_list.visible = visible

    def switch_wide_format_visibility(self, visible: bool):
        self.select_subject_col.visible = visible
        self.select_condition_col.visible = visible
        self.select_additional_index_cols.visible = visible
        self.sample_times_input.visible = visible

    def get_plate_format_column(self) -> pn.Column:
        return pn.Column(
            self.select_sample_id_col,
            self.select_data_col,
            self.select_id_col_names,
            self.regex_input,
            self.sample_times_input,
            self.fill_condition_list,
        )

    def get_wide_format_column(self) -> pn.Column:
        return pn.Column(
            self.select_subject_col,
            self.select_condition_col,
            self.select_additional_index_cols,
            self.sample_times_input,
        )

    def saliva_type_changed(self, _, event):
        self.saliva_type = event.new
        self.ready = self.is_ready()

    def parse_file_input(self, target, event):
        if ".csv" in self.upload_btn.filename:
            self.temporary_dataframe = self.handle_csv_file(self.upload_btn.value)
        elif ".xls" in self.upload_btn.filename:
            self.temporary_dataframe = self.handle_excel_file(self.upload_btn.value)
        if self.temporary_dataframe.empty:
            self.handle_error(ValueError("No data loaded"))
            return
        try:
            self.temporary_dataframe.dropna(axis=1, how="all", inplace=True)
            self.fill_options()
            self.show_param_input(True)
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            self.show_param_input(False)
            self.handle_error(e)

    def fill_options(self):
        if self.format == "Plate Format":
            self.select_sample_id_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_data_col.options = [""] + list(self.temporary_dataframe.columns)
            self.select_id_col_names.options = list(self.temporary_dataframe.columns)
        elif self.format == "Wide Format":
            self.select_subject_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_condition_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_additional_index_cols.options = list(
                self.temporary_dataframe.columns
            )

    def handle_error(self, e: Exception):
        pn.state.notifications.error("Error while loading data: " + str(e))
        self.ready = False
        # self.hide_param_input()

    def handle_csv_file(self, file) -> pd.DataFrame:
        try:
            return pd.read_csv(file, skiprows=2)
        except Exception as e:
            self.handle_error(e)
            return pd.DataFrame()

    def handle_excel_file(self, file) -> pd.DataFrame:
        try:
            df = pd.read_excel(file, skiprows=2)
            df.dropna(axis=1, how="all", inplace=True)
            return df
        except Exception as e:
            self.handle_error(e)
            return pd.DataFrame()

    def show_param_input(self, visibility: bool):
        self.select_saliva.visible = visibility
        if not visibility:
            self.switch_plate_format_visibility(False)
            self.switch_wide_format_visibility(False)
            return
        if self.format == "Plate Format":
            self.switch_plate_format_visibility(True)
            self.switch_wide_format_visibility(False)
        else:
            self.switch_plate_format_visibility(False)
            self.switch_wide_format_visibility(True)

    def panel(self):
        show_param_input = self.data is not None and len(self.data) > 0
        self.show_param_input(show_param_input)
        return self._view

    @param.output(
        ("condition_list", param.Dynamic),
        ("format", param.String),
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.List),
    )
    def output(self):
        if self.format == "Plate Format":
            self.process_plate_format()
        elif self.format == "Wide Format":
            self.process_wide_format()
        else:
            self.handle_error(ValueError("No format selected"))
        return (
            self.condition_list,
            self.format,
            self.data,
            self.saliva_type,
            self.sample_times_input.value,
        )

    def process_plate_format(self):
        try:
            self.data = load_saliva_plate(
                self.temporary_dataframe,
                self.saliva_type,
                (
                    self.select_sample_id_col.value
                    if self.select_sample_id_col.value != ""
                    else None
                ),
                (
                    self.select_data_col.value
                    if self.select_data_col.value != ""
                    else None
                ),
                (
                    self.select_id_col_names.value
                    if len(self.select_id_col_names.value) > 0
                    else None
                ),
                (self.regex_input.value if self.regex_input.value != "" else None),
                condition_list=(
                    self.condition_list
                    if self.condition_list is not None
                    and self.fill_condition_list.value
                    else None
                ),
            )
        except Exception as e:
            self.handle_error(e)

    def is_ready(self) -> bool:
        if self.saliva_type == "":
            return False
        return True

    def process_wide_format(self):
        try:
            self.data = load_saliva_wide_format(
                self.temporary_dataframe,
                self.select_saliva.value,
                self.select_subject_col.value,
                self.select_condition_col.value,
                self.select_additional_index_cols.value,
                self.sample_times_input.value,
            )
            self.ready = self.is_ready()
        except Exception as e:
            self.handle_error(e)

from biopsykit.utils.datatype_helper import SalivaMeanSeDataFrame
from fau_colors import cmaps
from numpy import ndarray



class ShowSalivaFeatures(SalivaBase):
    data_features = param.Dynamic(default=None)
    auc_args = {"remove_s0": False, "compute_auc_post": False, "sample_times": None}
    slope_args = {"sample_idx": None, "sample_labels": None}
    standard_features_args = {"group_cols": None, "keep_index": True}
    mean_se_args = {
        "test_times": [],
        "sample_times_absolute": False,
        "test_title": "Test",
        "remove_s0": False,
    }
    feature_boxplot_args = {
        "x": None,
        "hue": None,
        "feature": None,
        "palette": cmaps.faculties_light,
    }
    multi_feature_boxplot_args = {
        "hue": None,
        "hue_order": None,
        "features": None,
        "palette": cmaps.faculties_light,
    }
    feature_accordion_column = pn.Column(pn.Accordion(name="Features"))

    def get_feature_accordion(self) -> pn.Accordion:
        if self.data is None:
            return pn.Accordion()
        if self.saliva_type is None:
            return pn.Accordion()
        acc = pn.Accordion(name="Features", sizing_mode="stretch_width")
        acc.append(self.get_mean_se_element())
        acc.append(self.get_auc())
        acc.append(self.get_max_increase())
        acc.append(self.get_max_value())
        acc.append(self.get_standard_features())
        acc.append(self.get_initial_value())
        acc.append(self.get_feature_boxplot_element())
        acc.append(self.get_multi_feature_boxplot_element())
        return acc

    def get_mean_se_element(self):
        try:
            tab = pn.widgets.Tabulator(
                value=self.get_mean_se_df(),
                name="Mean and SE",
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
            )
            filename, button = tab.download_menu(
                text_kwargs={"name": "Enter filename", "value": "mean_se.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            download_btn = pn.widgets.FileDownload(
                label="Download",
                button_type="primary",
                callback=pn.bind(self.download_mean_se_figure),
                filename="figure.png",
            )
            col = pn.Column(name="Mean and SE")
            col.append(tab)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            col.append(pn.layout.Divider())
            col.append(self.edit_mean_se_figure())
            col.append(download_btn)
            return col
        except Exception as e:
            col = pn.Column(name="Mean and SE")
            col.append(pn.pane.Str(str(e)))
            return col

    def get_mean_se_df(self) -> SalivaMeanSeDataFrame:
        return bp.saliva.mean_se(
            data=self.data,
            saliva_type=self.saliva_type,
        )

    def edit_mean_se_figure(self):
        remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        sample_times_absolut = pn.widgets.Checkbox(
            name="Sample Times Absolute", value=False
        )
        test_times = pn.widgets.ArrayInput(name="Test Times", value=np.array([]))
        title = pn.widgets.TextInput(name="Title", value="Mean_SE_Figure")
        plot = pn.pane.Matplotlib(
            object=self.get_mean_se_figure(),
            format="svg",
            tight=True,
        )
        remove_s0.link(plot, callbacks={"value": self.update_mean_se_figure})
        sample_times_absolut.link(plot, callbacks={"value": self.update_mean_se_figure})
        test_times.link(plot, callbacks={"value": self.update_mean_se_figure})
        title.link(plot, callbacks={"value": self.update_mean_se_figure})
        return pn.Column(remove_s0, sample_times_absolut, test_times, title, plot)

    def update_mean_se_figure(self, target, event):
        if event.cls.name == "Title":
            self.mean_se_args["test_title"] = event.new
        elif event.cls.name == "Test Times":
            self.mean_se_args["test_times"] = list(event.new)
        elif event.cls.name == "Sample Times Absolute":
            self.mean_se_args["sample_times_absolute"] = event.new
        elif event.cls.name == "Remove S0":
            self.mean_se_args["remove_s0"] = event.new
        target.object = self.get_mean_se_figure()

    def get_mean_se_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, ax = bp.protocols.plotting.saliva_plot(
                self.get_mean_se_df(),
                saliva_type=self.saliva_type,
                sample_times=self.sample_times,
                **self.mean_se_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure(figsize=(10, 10))

    def download_mean_se_figure(self):
        buf = io.BytesIO()
        fig = self.get_mean_se_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def get_feature_boxplot_element(self) -> pn.Column:
        try:
            plot = pn.pane.Matplotlib(self.get_feature_boxplot_figure(), format="svg")
            col = pn.Column(name="Feature Boxplot")
            x_select = pn.widgets.Select(
                name="x",
                value=None,
                options=list(x.name for x in self.data_features.index.levels),
            )
            hue_textInput = pn.widgets.TextInput(name="hue", value="condition")
            feature_multichoice = pn.widgets.MultiChoice(
                name="feature", value=[], options=[]
            )
            hue_textInput.link(
                plot, callbacks={"value": self.update_feature_boxplot_figure}
            )
            x_select.link(plot, callbacks={"value": self.update_feature_boxplot_figure})
            feature_multichoice.link(
                plot, callbacks={"value": self.update_feature_boxplot_figure}
            )
            download_btn = pn.widgets.FileDownload(
                label="Download",
                button_type="primary",
                callback=pn.bind(self.download_boxplot_figure),
                filename="mean_se_figure.png",
            )
            col.append(
                pn.Row(
                    pn.Column(hue_textInput, x_select, feature_multichoice),
                    plot,
                )
            )
            col.append(pn.layout.Divider())
            col.append(download_btn)
            return col
        except Exception as e:
            col = pn.Column(name="Feature Boxplot")
            col.append(pn.pane.Str(str(e)))
            return col

    def download_boxplot_figure(self):
        buf = io.BytesIO()
        fig = self.get_feature_boxplot_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def update_feature_boxplot_figure(self, target, event):
        if event.cls.name == "x":
            self.feature_boxplot_args["x"] = event.new
        elif event.cls.name == "hue":
            self.feature_boxplot_args["hue"] = event.new
        elif event.cls.name == "feature":
            self.feature_boxplot_args["feature"] = event.new
        target.object = self.get_feature_boxplot_figure()

    def get_feature_boxplot_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, _ = bp.protocols.plotting.saliva_feature_boxplot(
                data=self.data_features,
                saliva_type=self.saliva_type,
                **self.feature_boxplot_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure()

    def get_multi_feature_boxplot_element(self) -> pn.Column:
        try:
            plot = pn.pane.Matplotlib(
                self.get_multi_feature_boxplot_figure(),
                format="svg",
            )
            col = pn.Column(name="Multi Feature Boxplot")
            hue_multiChoice = pn.widgets.MultiChoice(
                name="hue",
                value=[],
                options=list(x.name for x in self.data_features.index.levels),
                max_items=1,
            )
            hue_order_multichoice = pn.widgets.MultiChoice(
                name="hue_order",
                value=[],
                max_items=1,
                options=list(x.values for x in self.data_features.index.levels),
            )
            features_multichoice = pn.widgets.MultiChoice(
                name="features",
                value=[],
                options=list(
                    itertools.chain(
                        *list(x.values for x in self.data_features.index.levels)
                    )
                ),
            )
            hue_multiChoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            hue_order_multichoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            features_multichoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            download_btn = pn.widgets.FileDownload(
                label="Download",
                button_type="primary",
                callback=pn.bind(self.download_multi_boxplot_figure),
                filename="figure.png",
            )
            col.append(
                pn.Row(
                    pn.Column(
                        hue_multiChoice, hue_order_multichoice, features_multichoice
                    ),
                    plot,
                )
            )
            col.append(pn.layout.Divider())
            col.append(download_btn)
            return col
        except Exception as e:
            col = pn.Column(name="Multi Feature Boxplot")
            col.append(pn.pane.Str(str(e)))
            return col

    def download_multi_boxplot_figure(self):
        buf = io.BytesIO()
        fig = self.get_multi_feature_boxplot_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def update_multi_feature_boxplot_figure(self, target, event):
        if event.cls.name == "features":
            new_value = event.new if len(event.new) > 0 else None
        else:
            new_value = event.new[0] if len(event.new) > 0 else None
        if isinstance(new_value, ndarray):
            new_value = new_value.tolist()
        self.multi_feature_boxplot_args[event.cls.name] = new_value
        target.object = self.get_multi_feature_boxplot_figure()

    def get_multi_feature_boxplot_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, _ = bp.protocols.plotting.saliva_multi_feature_boxplot(
                data=self.data_features,
                saliva_type=self.saliva_type,
                **self.multi_feature_boxplot_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure()

    def filter_auc(self, target, event):
        if event is None or event.cls is None:
            return
        if event.cls.name == "Remove S0":
            self.auc_args["remove_s0"] = event.new
        elif event.cls.name == "Compute AUC Post":
            self.auc_args["compute_auc_post"] = event.new
        elif event.cls.name == "Sample Times":
            self.auc_args["sample_times"] = event.new
        else:
            return
        auc_df = bp.saliva.auc(
            data=self.data,
            saliva_type=self.saliva_type,
            **self.auc_args,
        )
        target.value = auc_df

    def get_auc(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(
                name="Remove S0", value=False, align=("start", "start")
            )
            compute_auc_post = pn.widgets.Checkbox(name="Compute AUC Post", value=False)
            auc_df = bp.saliva.auc(
                data=self.data,
                saliva_type=self.saliva_type,
                sample_times=self.sample_times,
                remove_s0=switch_remove_s0.value,
                compute_auc_post=compute_auc_post.value,
            )
            auc_tabulator = pn.widgets.Tabulator(
                auc_df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
                header_align="right",
            )
            switch_remove_s0.link(
                auc_tabulator,
                callbacks={"value": self.filter_auc},
            )
            compute_auc_post.link(auc_tabulator, callbacks={"value": self.filter_auc})
            filename, button = auc_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "auc.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="AUC")
            col.append(
                pn.Row(
                    "**Remove s0**",
                    switch_remove_s0,
                    pn.layout.HSpacer(),
                    align=("center"),
                )
            )
            col.append(pn.Row("**Compute AUC Post**", compute_auc_post))
            col.append(auc_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="AUC")
            col.append(pn.pane.Str(str(e)))
            return col

    def max_value_switch_removes0(self, target, event):
        target.value = bp.saliva.max_value(self.data, remove_s0=event.new)

    def get_max_value(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.max_value(self.data, remove_s0=switch_remove_s0.value)
            max_value_tabulator = pn.widgets.Tabulator(
                df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
                header_align="right",
            )
            filename, button = max_value_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "max_value.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            switch_remove_s0.link(
                max_value_tabulator, callbacks={"value": self.max_value_switch_removes0}
            )
            col = pn.Column(name="Max Value")
            col.append(pn.Row("**Remove s0**", switch_remove_s0, pn.layout.HSpacer()))
            col.append(max_value_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Max Value")
            col.append(pn.pane.Str(str(e)))
            return col

    def change_standard_feature(self, target, event):
        if event is None or event.cls is None:
            return
        if event.cls.name == "Group Columns":
            self.standard_features_args["group_cols"] = (
                event.new if event.new != [] else None
            )
        elif event.cls.name == "Keep Index":
            self.standard_features_args["keep_index"] = event.new
        else:
            return
        # try:
        df = bp.saliva.standard_features(
            data=self.data,
            saliva_type=self.saliva_type,
            **self.standard_features_args,
        )
        target.value = df
        # except Exception as e:
        #     pn.state.notifications.error(e)
        #     target.value = pd.DataFrame()

    def get_standard_features(self) -> pn.Column:
        try:
            group_cols = pn.widgets.MultiChoice(
                name="Group Columns", value=[], options=list(self.data.columns)
            )
            keep_index = pn.widgets.Checkbox(name="Keep Index", value=True)
            df = bp.saliva.standard_features(
                self.data,
                saliva_type=self.saliva_type,
                group_cols=(group_cols.value if group_cols.value != [] else None),
                keep_index=keep_index.value,
            )
            standard_features_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            group_cols.link(
                standard_features_tabulator,
                callbacks={"value": self.change_standard_feature},
            )
            keep_index.link(
                standard_features_tabulator,
                callbacks={"value": self.change_standard_feature},
            )
            filename, button = standard_features_tabulator.download_menu(
                text_kwargs={
                    "name": "Enter filename",
                    "value": "standard_features.csv",
                },
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="Standard Features")
            col.append(group_cols)
            col.append(keep_index)
            col.append(standard_features_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Standard Features")
            col.append(pn.pane.Str(str(e)))
            return col

    def initial_value_switch_removes0(self, target, event):
        target.value = bp.saliva.initial_value(self.data, remove_s0=event.new)

    def get_initial_value(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.initial_value(self.data, remove_s0=switch_remove_s0.value)
            initial_value_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            filename, button = initial_value_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "initial_value.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            switch_remove_s0.link(
                initial_value_tabulator,
                callbacks={"value": self.initial_value_switch_removes0},
            )
            col = pn.Column(name="Initial Value")
            col.append(pn.Row("**Remove s0**", switch_remove_s0))
            col.append(initial_value_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Initial Value")
            col.append(pn.pane.Str(str(e)))
            return col

    def max_increase_switch_removes0(self, target, event):
        target.value = bp.saliva.max_increase(self.data, remove_s0=event.new)

    def get_max_increase(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.max_increase(self.data)
            max_increase_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            switch_remove_s0.link(
                max_increase_tabulator,
                callbacks={"value": self.max_increase_switch_removes0},
            )
            filename, button = max_increase_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "max_increase.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="Max Increase")
            col.append(pn.Row("**Remove s0**", switch_remove_s0))
            col.append(max_increase_tabulator)
            col.append(pn.Row(filename, button))
            return col
        except Exception as e:
            col = pn.Column(name="Max Increase")
            col.append(pn.pane.Str(str(e)))
            return col

    def get_slope(self) -> pn.Column:
        sample_times_input = pn.widgets.ArrayInput(
            name="Sample Times",
            value=self.sample_times,
            placeholder="Enter the sample times in Array form, e.g. [-30, -1, 30, 40]",
        )
        sample_idx = pn.widgets.ArrayInput(
            name="Sample Index", value=[1, 4], placeholder="Enter the sample index"
        )
        slope_df = bp.saliva.slope(
            self.data,
            sample_idx=sample_idx.value,
            sample_times=sample_times_input.value,
            sample_labels=None,
        )
        col = pn.Column(name="Slope")
        col.append(sample_times_input)
        col.append(sample_idx)
        col.append(
            pn.widgets.Tabulator(
                slope_df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

    def __init__(self, **params):
        params["HEADER_TEXT"] = SHOW_FEATURES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(SHOW_FEATURES_TEXT)
        self._view = pn.Column(self.header, self.feature_accordion_column)

    def panel(self):
        if self.data_features is None and self.data is not None:
            self.data_features = bp.saliva.standard_features(self.data)
            self.data_features = bp.saliva.utils.saliva_feature_wide_to_long(
                self.data_features, saliva_type=self.saliva_type
            )
        self.feature_accordion_column.__setitem__(0, self.get_feature_accordion())
        return self._view

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class SalivaPipeline:
    pipeline = None
    name = "Saliva"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline()
        self.pipeline.add_stage(
            "Ask for Format",
            AskForFormat(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage(
            "Ask for Subject Condition List",
            AskToLoadConditionList(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Add Condition List",
            AddConditionList(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Load Saliva Data",
            LoadSalivaData(),
        )
        self.pipeline.add_stage("Show Features", ShowSalivaFeatures())

        self.pipeline.define_graph(
            {
                "Ask for Format": "Ask for Subject Condition List",
                "Ask for Subject Condition List": (
                    "Add Condition List",
                    "Load Saliva Data",
                ),
                "Add Condition List": "Load Saliva Data",
                "Load Saliva Data": "Show Features",
            }
        )




class PlotResults(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)



SLEEP_MAX_STEPS = 7

POSSIBLE_DEVICES = [
    "Polysomnography",
    "Other IMU Device",
    "Withings",
]


UPLOAD_PARAMETERS_TEXT = "# Set sleep data parameters \\n Below you can set the parameters for the sleep data. If you are unsure, you can leave the default values."
CHOOSE_DEVICE_TEXT = "# Choose the recording device \\n Below you can choose the device you used to record your sleep data. If you used a different device, please choose 'Other IMU Device'."
ZIP_OR_FOLDER_TEXT = "# File or Folder? \\n If you want to upload a complete folder, please zip it first. You can then upload the zip file in the following step."
UPLOAD_SLEEP_DATA_TEXT = "# Upload your sleep data \\n Please upload your sleep data in the following step. You can either upload a single file or a zip file containing all your files."



class SleepBase(param.Parameterized):
    selected_device = param.String(default="")
    step = param.Integer(default=1)
    parsing_parameters = {
        "Withings": {
            "data_source": ["heart_rate", "respiration_rate", "sleep_state", "snoring"],
            "timezone": [
                "None",
            ]
            + list(pytz.all_timezones),
            "split_into_nights": True,
        },
        "Polysomnography": {
            "datastreams": None,
            "tz": [
                "None",
            ]
            + list(pytz.all_timezones),
        },
        "Other IMU Device": {
            # "handle_counter_inconsistency": ["raise", "warn", "ignore"],
            "tz": [
                "None",
            ]
            + list(pytz.all_timezones),
        },
    }
    selected_parameters = param.Dynamic(
        default={
            "Withings": {
                "data_source": "heart_rate",
                "timezone": None,
                "split_into_nights": True,
            },
            "Polysomnography": {
                "datastreams": None,
                "tz": None,
            },
            "Other IMU Device": {
                # "handle_counter_inconsistency": ["raise", "warn", "ignore"],
                "tz": None,
            },
        }
    )
    data = param.Dynamic(default={})

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, SLEEP_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def add_data(self, parsed_file, filename: str):
        if filename in self.data.keys():
            self.data.remove(filename)
        self.data[filename] = parsed_file

    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
    )
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
        )


class ZipFolder(SleepBase):
    def __init__(self, **params):
        params["HEADER_TEXT"] = ZIP_OR_FOLDER_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(ZIP_OR_FOLDER_TEXT)
        self._view = pn.Column(self.header)

    def panel(self):
        return self._view


from io import BytesIO, StringIO
from zipfile import ZipFile




class UploadSleepData(SleepBase):
    fs = param.Dynamic(default=None)
    ready = param.Boolean(default=False)
    accepted_file_types = {
        "Polysomnography": ".edf, .zip",
        "Other IMU Device": ".bin, .zip",
        "Withings": ".csv, .zip",
    }
    upload_data = pn.widgets.FileInput(
        name="Upload sleep data",
        multiple=False,
    )
    next_page = param.Selector(
        default="Process Data",
        objects=["Process Data", "Convert Acc to g"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_SLEEP_DATA_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(UPLOAD_SLEEP_DATA_TEXT)
        self.upload_data.link(self, callbacks={"value": self.process_data})
        self._view = pn.Column(self.header, self.upload_data)

    def process_data(self, target, _):
        try:
            if self.upload_data.value is None:
                self.ready = False
                pn.state.notifications.error("Please upload a file")
            elif self.selected_device == "Polysomnography":
                self.parse_psg()
            elif self.selected_device == "Other IMU Device":
                self.parse_other_imu()
            elif self.selected_device == "Withings":
                self.parse_withings()
            else:
                pn.state.notifications.error("Please choose a device")
                self.ready = False
                return
            self.ready = True
            pn.state.notifications.success("Successfully loaded data")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def parse_psg(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        elif self.upload_data.filename.endswith(".edf"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        else:
            pn.state.notifications.error("Please upload a zip or edf file")
            self.ready = False

    def parse_other_imu(self):
        if self.upload_data.filename.endswith(".bin"):
            dataset = NilsPodAdapted.from_bin_file(
                filepath_or_buffer=BytesIO(self.upload_data.value),
                legacy_support="resolve",
                **self.selected_parameters[self.selected_device],
            )
            df, _ = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
            self.add_data(df, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".csv"):
            string_io = StringIO(self.upload_data.value.decode("utf-8"))
            dataset = pd.read_csv(string_io)
            self.add_data(dataset, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".zip"):
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".bin"):
                    dataset = NilsPodAdapted.from_bin_file(
                        filepath_or_buffer=BytesIO(input_zip.read(file)),
                        **self.selected_parameters[self.selected_device],
                    )
                    datasets.append(dataset)
                elif file.filename.endswith(".csv"):
                    string_io = StringIO(str(input_zip.open(file)))
                    dataset = pd.read_csv(string_io)
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        self.ready = True
        pn.state.notifications.success("Successfully loaded data")

    def parse_withings(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".csv"):
                    dataset = self.load_withings(
                        file=bytes(input_zip.read(file)),
                        filename=file.filename,
                    )
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".csv"):
            dataset = self.load_withings(
                file=bytes(self.upload_data.value), filename=self.upload_data.filename
            )
            self.add_data(dataset, self.upload_data.filename)
        self.ready = True
        pn.state.notifications.success("Successfully loaded data")

    def load_withings(self, file: bytes, filename):
        dataset = load_withings_sleep_analyzer_raw_file(
            file=file,
            file_name=filename,
            **self.selected_parameters[self.selected_device]
            # data_source=self.selected_parameters["data_source"],
            # timezone=self.selected_parameters["timezone"],
            # split_into_nights=self.selected_parameters["split_into_nights"],
        )
        return dataset

    def panel(self):
        if self.selected_device == "Other IMU Device":
            self.next_page = "Convert Acc to g"
        self.upload_data.accept = self.accepted_file_types[self.selected_device]
        return self._view






class ChooseRecordingDevice(SleepBase):
    possible_devices = [""] + POSSIBLE_DEVICES
    ready = param.Boolean(default=False)
    device_selector = pn.widgets.Select(
        name="Device",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHOOSE_DEVICE_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(CHOOSE_DEVICE_TEXT)
        self.device_selector.options = self.possible_devices
        self.device_selector.link(self, callbacks={"value": self.device_changed})
        self._view = pn.Column(self.header, self.device_selector)

    def device_changed(self, _, event):
        self.selected_device = event.new
        self.ready = bool(event.new)

    def panel(self):
        self.device_selector.value = self.selected_device
        return self._view



class ZipFolder(SleepBase):
    def __init__(self, **params):
        params["HEADER_TEXT"] = ZIP_OR_FOLDER_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(ZIP_OR_FOLDER_TEXT)
        self._view = pn.Column(self.header)

    def panel(self):
        return self._view



class SetSleepDataParameters(SleepBase):
    parameter_column = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(UPLOAD_PARAMETERS_TEXT)
        self._view = pn.Column(self.header, self.parameter_column)

    def get_parameter_column_for_selected_device(self) -> pn.Column:
        col = pn.Column()
        if self.selected_device == "":
            return col
        possible_parameters = self.parsing_parameters[self.selected_device]
        for parameter, options in possible_parameters.items():
            set_value = self.selected_parameters[self.selected_device][parameter]
            if options is None:
                continue
            if isinstance(options, list):
                widget = pn.widgets.Select(
                    name=parameter,
                    options=options,
                    value=set_value if set_value is not None else options[0],
                )
            elif isinstance(options, bool):
                widget = pn.widgets.Checkbox(
                    name=parameter,
                    value=set_value,
                )
            else:
                continue
            widget.link(widget.name, callbacks={"value": self.parameter_changed})
            col.append(widget)
        return col

    def parameter_changed(self, target, event):
        if self.selected_device == "":
            pn.state.notifications.error("No device selected")
            return
        if target not in self.parsing_parameters[self.selected_device].keys():
            pn.state.notifications.error(
                f"{target} not found in parameters for {self.selected_device}"
            )
            return
        if event.new == "None":
            self.selected_parameters[self.selected_device][target] = None
        else:
            self.selected_parameters[self.selected_device][target] = event.new
        pn.state.notifications.success(f"{target} changed to {event.new}")

    def panel(self):
        if len(self.parameter_column.objects) == 0:
            self.parameter_column.append(
                self.get_parameter_column_for_selected_device()
            )
        else:
            self.parameter_column.__setitem__(
                0, self.get_parameter_column_for_selected_device()
            )
        return self._view
from io import BytesIO, StringIO
from zipfile import ZipFile




class UploadSleepData(SleepBase):
    fs = param.Dynamic(default=None)
    ready = param.Boolean(default=False)
    accepted_file_types = {
        "Polysomnography": ".edf, .zip",
        "Other IMU Device": ".bin, .zip",
        "Withings": ".csv, .zip",
    }
    upload_data = pn.widgets.FileInput(
        name="Upload sleep data",
        multiple=False,
    )
    next_page = param.Selector(
        default="Process Data",
        objects=["Process Data", "Convert Acc to g"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_SLEEP_DATA_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(UPLOAD_SLEEP_DATA_TEXT)
        self.upload_data.link(self, callbacks={"value": self.process_data})
        self._view = pn.Column(self.header, self.upload_data)

    def process_data(self, target, _):
        try:
            if self.upload_data.value is None:
                self.ready = False
                pn.state.notifications.error("Please upload a file")
            elif self.selected_device == "Polysomnography":
                self.parse_psg()
            elif self.selected_device == "Other IMU Device":
                self.parse_other_imu()
            elif self.selected_device == "Withings":
                self.parse_withings()
            else:
                pn.state.notifications.error("Please choose a device")
                self.ready = False
                return
            self.ready = True
            pn.state.notifications.success("Successfully loaded data")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def parse_psg(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        elif self.upload_data.filename.endswith(".edf"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        else:
            pn.state.notifications.error("Please upload a zip or edf file")
            self.ready = False

    def parse_other_imu(self):
        if self.upload_data.filename.endswith(".bin"):
            dataset = NilsPodAdapted.from_bin_file(
                filepath_or_buffer=BytesIO(self.upload_data.value),
                legacy_support="resolve",
                **self.selected_parameters[self.selected_device],
            )
            df, _ = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
            self.add_data(df, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".csv"):
            string_io = StringIO(self.upload_data.value.decode("utf-8"))
            dataset = pd.read_csv(string_io)
            self.add_data(dataset, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".zip"):
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".bin"):
                    dataset = NilsPodAdapted.from_bin_file(
                        filepath_or_buffer=BytesIO(input_zip.read(file)),
                        **self.selected_parameters[self.selected_device],
                    )
                    datasets.append(dataset)
                elif file.filename.endswith(".csv"):
                    string_io = StringIO(str(input_zip.open(file)))
                    dataset = pd.read_csv(string_io)
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        self.ready = True
        pn.state.notifications.success("Successfully loaded data")

    def parse_withings(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".csv"):
                    dataset = self.load_withings(
                        file=bytes(input_zip.read(file)),
                        filename=file.filename,
                    )
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".csv"):
            dataset = self.load_withings(
                file=bytes(self.upload_data.value), filename=self.upload_data.filename
            )
            self.add_data(dataset, self.upload_data.filename)
        self.ready = True
        pn.state.notifications.success("Successfully loaded data")

    def load_withings(self, file: bytes, filename):
        dataset = load_withings_sleep_analyzer_raw_file(
            file=file,
            file_name=filename,
            **self.selected_parameters[self.selected_device]
            # data_source=self.selected_parameters["data_source"],
            # timezone=self.selected_parameters["timezone"],
            # split_into_nights=self.selected_parameters["split_into_nights"],
        )
        return dataset

    def panel(self):
        if self.selected_device == "Other IMU Device":
            self.next_page = "Convert Acc to g"
        self.upload_data.accept = self.accepted_file_types[self.selected_device]
        return self._view

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class SleepPipeline:
    name = "Sleep"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline()
        self.pipeline.add_stage(
            "Ask for Recording Device",
            ChooseRecordingDevice(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage(
            "Set Parsing Parameters",
            SetSleepDataParameters(),
        )

        self.pipeline.add_stage("Ask for Format", ZipFolder())

        self.pipeline.add_stage(
            "Upload Sleep Data",
            UploadSleepData(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )

        # self.pipeline.add_stage(
        #     "Ask for Subject Condition List",
        #     AskToLoadConditionList(),
        #     ready_parameter="ready",
        #     next_parameter="next_page",
        #     auto_advance=True,
        # )

        self.pipeline.define_graph(
            {
                "Ask for Recording Device": "Set Parsing Parameters",
                "Set Parsing Parameters": "Ask for Format",
                "Ask for Format": "Upload Sleep Data",
            }
        )




class ResultsPreview(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)

    def show_results(self) -> pn.Column:
        col = pn.Column()
        if len(self.processed_data) == 1:
            col.append(self.show_individual_results(self.processed_data[0]))
            return col
        result = 1
        accordion = pn.Accordion()
        for data in self.processed_data:
            results_col = self.show_individual_results(data)
            accordion.append((f"Result {result}", results_col))
            result += 1

    @staticmethod
    def show_individual_results(data) -> pn.Column:
        col = pn.Column()
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                col.append(pn.widgets.Tabulator(value, name=key))
                col.append(pn.layout.Divider())
            elif isinstance(value, list):
                text = pn.widgets.StaticText(name=key, value=value)
                col.append(text)
                col.append(pn.layout.Divider())
            elif isinstance(value, dict) and key == "sleep_endpoints":
                col.append(
                    pn.widgets.Tabulator(
                        bp.sleep.sleep_endpoints.endpoints_as_df(value), name=key
                    )
                )
                col.append(pn.layout.Divider())
            else:
                text = pn.widgets.StaticText(name=key, value=value)
                col.append(text)
                col.append(pn.layout.Divider())
        return col

    def panel(self):
        text = "# Results Preview \\n Below you can see a preview of the results. If you are satisfied with the results, you can click 'Save Results' to save the results to your local machine."
        return pn.Column(pn.pane.Markdown(text), self.show_results())




class ProcessDataParameters(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)
    processing_parameters = {}
    possible_processing_parameters = {
        "acceleration": {
            "convert_to_g": True,
            "algorithm_type": ["Cole/Kripke"],
            "epoch_length": 60,
        },
        "actigraph": {
            "algorithm_type": ["Cole/Kripke"],
            "bed_interval": [],
        },
    }

    # TODO -> wann acceleration, wann actigraph?
    def show_parameters(self) -> pn.Column:
        params = self.possible_processing_parameters["acceleration"]
        col = pn.Column()
        for parameter, options in params.items():
            if options is None:
                continue
            if isinstance(options, list):
                if parameter == "algorithm_type":
                    widget = pn.widgets.Select(
                        name=parameter,
                        options=options,
                    )
                    widget.param.watch(self.parameter_changed, "value")
                    col.append(widget)
                else:
                    widget = pn.widgets.MultiChoice(
                        name=parameter,
                        options=options,
                    )
                    widget.param.watch(self.parameter_changed, "value")
                    col.append(widget)
            elif isinstance(options, bool):
                widget = pn.widgets.Checkbox(
                    name=parameter,
                    value=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
            elif isinstance(options, int):
                widget = pn.widgets.IntInput(
                    name=parameter,
                    value=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
        return col

    def parameter_changed(self, event):
        self.processing_parameters[event.obj.name] = event.new

    # TODO brauchen noch sampling_rate und zuordnung zwischen data
    @param.output(
        ("selected_device", param.String),
        ("data", param.Dynamic),
        ("processed_data", param.Dynamic),
    )
    def output(self):
        self.processed_data = []
        for ds in self.data:
            results = bp.sleep.sleep_processing_pipeline.predict_pipeline_actigraph(
                data=ds, **self.processing_parameters
            )
            self.processed_data.append(results)
        return (self.selected_device, self.data, self.processed_data)

    def panel(self):
        text = "# Processing Parameters \\n Below you can choose the processing parameters for your data. If you are unsure, just leave the default values."
        return pn.Column(pn.pane.Markdown(text), self.show_parameters())


WELCOME_TEXT = (
    "# Welcome to the BioPsyKit Dashboard \\n\\n"
    "## Here you can analyse your Data using the BioPsyKit without any manual programming. \\n"
    "Please select below one of the Signals you want to analyse. "
    "The corresponding guide will help you to get the best out of your data."
)



WELCOME_TEXT = (
    "# Welcome to the BioPsyKit Dashboard \\n\\n"
    "## Here you can analyse your Data using the BioPsyKit without any manual programming. \\n"
    "Please select below one of the Signals you want to analyse. "
    "The corresponding guide will help you to get the best out of your data."
)


from biopsykit.protocols import CFT
from matplotlib import pyplot as plt


PHYSIOLOGICAL_MAX_STEPS = 12
PHYSIOLOGICAL_SIGNAL_OPTIONS = ["", "ECG", "RSP", "EEG"]
TIMEZONES = ["None Selected"] + list(pytz.all_timezones)
PHYSIOLOGICAL_HW_OPTIONS = ["NilsPod", "BioPac"]

HRV_METHODS = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]

OUTLIER_METHODS = [
    "quality",
    "artifact",
    "physiological",
    "statistical_rr",
    "statistical_rr_diff",
]
EDR_TYPES = ["peak_trough_mean", "peak_trough_diff", "peak_peak_interval"]

SESSION_TEXT = (
    "# Number of Sessions \\n"
    "In this step you can define if your data consists of a single Session or multiple Sessions. \\n\\n"
    "In this context a single Session is defined that only one Sensor is used, "
    "while multiple Sessions describe that two or more sensors are used. \\n"
)

SIGNAL_TYPE_TEXT = "# Selecting Physiological Signal Type"
SELECT_CFT_TEXT = (
    "# Select CFT Sheet \\n\\n"
    "This step allows you to select a CFT sheet from a list "
    "of available sheets."
)

SELECT_FREQUENCY_TEXT = (
    "# Set Frequency Bands"
    "In this step you can set the frequency bands for the analysis. "
    "The default values are the standard frequency bands for EEG analysis. "
    "You can change the values by clicking on the text field and entering the desired value. "
    "The values are in Hz."
)

RECORDINGS_TEXT = (
    "# Number of Recordings \\n"
    "After you defined the kind of Sessions, in this step you will set if your data"
    "consists of a single Recording or multiple recordings.\\n\\n"
    "A single Recording means, that you only have one file per subject and multiple Recording"
    "is defined as two or more files per subject. \\n"
)
PROCESSING_PREVIEW_TEXT = (
    "# Preview of the Results \\n \\n"
    "Below you can find a short summary of the analyzed data "
    "(Preview of the Dataframe, and several statistical values)."
)
PROCESS_HRV_TEXT = (
    "# Processing HRV \\n \\n"
    "If you want to additionally process the Heart Rate variability, "
    "you can select the matching parameters and then hit the "
    "process button, and then proceed. Otherwise, you can skip "
    "this step and go to the next stage. "
)
ASK_PROCESS_HRV_TEXT = (
    "# Processing HRV \\n \\n"
    "If you want to additionally process the Heart Rate variability, "
    "you can select the matching parameters and then "
    "hit the process button, and then proceed. "
    "Otherwise, you can skip this step and go to the next stage. \\n \\n"
)
ASK_DETECT_OUTLIER_TEXT = "# Do you want to check for outliers?"

OUTLIER_DETECTION_TEXT = (
    "# Outlier Detection \\n\\n"
    "# # In this stage the ECG signal will be processed. This will be done in three steps: "
    "Filtering, R-peak detection, Outlier correction. \\n\\n"
    "Below you can select the outlier correction methods, which consist of: \\n"
    "- Correlation: Computes cross-correlation coefficient between every single beat and the average of all"
    " detected beats. Marks beats as outlier if cross-correlation coefficient is below a certain threshold. \\n"
    "- Quality: Uses the ECG_Quality indicator is below a certain threshold. \\n"
    "- Artifact: Artifact detection based on Berntson et al. (1990)."
    "- Physiological: Physiological outlier removal. "
    "Marks beats if their heart rate is above or below a threshold that "
    "is very unlikely to be achieved physiologically. \\n"
    "- Statistical rr: Marks beats as outlier if the RR interval is above or below a certain threshold. \\n"
    "Statistical outlier removal based on RR intervals. Marks beats as outlier if the "
    "intervals are within the xx% highest or lowest values. Values are removed based on the z-score; "
    "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); "
    "2.576 => 1% (0.5% highest, 0.5% lowest values). \\n"
    "- Statistical rr diff: Statistical outlier removal based on successive differences "
    "of RR intervals. Marks beats as outlier if the difference of successive RR intervals "
    "are within the xx% highest or lowest heart rates. Values are removed based on the z-score; "
    "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); 2.576 => 1% "
    "(0.5% highest, 0.5% lowest values). \\n"
    "Furthermore, you can set the parameters for the outlier detection methods you chose down below. "
    "If you don't change anything the default values for the corresponding method will be used. \\n"
)

FILE_UPLOAD_TEXT = (
    "# Upload your session File \\n"
    "## The supported File formats are .bin, .csv, and you can also choose Folders.\\n"
    "After your upload your file will also be checked if it contains the necessary columns.\\n"
)

DOWNLOAD_RESULT_TEXT = "# Download Result \\n"
DATA_ARRIVED_TEXT = (
    "# Files uploaded successfully \\n"
    "Below is a short summary of the files which you uploaded."
    "These files can be further analysed in the following steps."
)

COMPRESS_FILES_TEXT = (
    "# Compress your Files\\n"
    "Because you selected, that you want to analyse more than one File,"
    "you have to compress the content of your Folder into one .zip File.\\n"
    "Please do that before proceeding to the next step.\\n"
)
ASK_ADD_TIMES_TEXT = (
    "# Do you want to add Phases for your Data?\\n"
    "If you want to upload an Excel oder CSV File, or if you want to manually add Phases "
    "to your data then click on the Add Times Button otherwise skip"
)
ADD_TIMES_TEXT = "# Select Times"
PRESTEP_PROCESSING_TEXT = (
    "# Processing \\n"
    "Im nächsten Schritt werden die Daten verarbeitet, dieser Schritt dauert einen Moment :)."
)

SET_RSP_PARAMETERS_TEXT = (
    "# RSP Parameters\\n"
    "Here you can set the different parameters for the RSP analysis. You may select if the data is "
    "a Raw respiration signal or if it has to be estimated by the ECG. \\n"
    "You ma also choose the method used to estimate the respiration signal from the ECG. \\n"
)



class PhysiologicalBase(param.Parameterized):
    artifact = pn.widgets.FloatInput(name="artifact", value=0)
    correlation = pn.widgets.FloatInput(name="correlation", value=0.3)
    correct_rpeaks = param.Boolean(default=False)
    cft_sheets = param.Dynamic()
    cft_processor = {}
    data = param.Dynamic()
    data_processed = param.Boolean(default=False)
    dict_hr_subjects = {}
    ecg_processor = param.Dynamic()
    eeg_processor = {}
    estimate_rsp = param.Boolean(default=False)
    estimate_rsp_method = param.String(default="peak_trough_mean")
    freq_bands = param.Dynamic(default=None)
    hardware = param.Selector(
        label="Select the Hardware with which you recorded your data",
        objects=PHYSIOLOGICAL_HW_OPTIONS,
        default="NilsPod",
    )
    hr_data = None
    hrv_types = param.List(default=None)
    hrv_index_name = param.String(default="")
    original_data = param.Dynamic()
    progress = pn.indicators.Progress(
        name="Progress", height=20, sizing_mode="stretch_width"
    )
    phase_series = param.Dynamic()
    physiological_upper = pn.widgets.IntInput(name="physiological_upper", value=200)
    physiological_lower = pn.widgets.IntInput(name="physiological_lower", value=45)
    recording = param.String(default="Single Recording")
    rsp_processor = {}
    sampling_rate = param.Number(default=-1.0)
    synced = param.Boolean(default=False)
    skip_hrv = param.Boolean(default=True)
    session = param.String(default="Single Session")
    sensors = param.Dynamic()
    subject = param.Dynamic()
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )
    signal = param.String(default="")
    step = param.Integer(default=1)
    subject_time_dict = param.Dynamic(default={})
    statistical_param = pn.widgets.FloatInput(name="Statistical:", value=2.576)
    statistical_rr = pn.widgets.FloatInput(name="statistical_rr", value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name="statistical_rr_diff", value=1.96)
    skip_outlier_detection = param.Boolean(default=True)
    selected_outlier_methods = param.Dynamic(default=None)
    textHeader = ""
    times = None
    timezone = param.String(default="Europe/Berlin")
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    trimmed_data = param.Dynamic()
    max_steps = PHYSIOLOGICAL_MAX_STEPS
    outlier_params = param.Dynamic(default=None)
    quality = pn.widgets.FloatInput(name="quality", value=0.4)

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, PHYSIOLOGICAL_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    @staticmethod
    def get_progress(step) -> pn.indicators.Progress:
        return pn.indicators.Progress(
            name="Progress", height=20, sizing_mode="stretch_width", max=12, value=step
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)

    def select_vp_changed(self, _, event):
        self.subject = str(event.new)

    def dict_to_column(self):
        if self.session == "Single Session" and len(self.subject_time_dict.keys()) > 1:
            self.select_vp.options = list(self.subject_time_dict.keys())
            self.select_vp.visible = True
            self.select_vp.link(
                "subject",
                callbacks={"value": self.select_vp_changed},
            )
            self.subject = list(self.subject_time_dict.keys())[0]
            self.ready = True
        timestamps = []
        for subject in self.subject_time_dict.keys():
            col = pn.Column()
            for condition in self.subject_time_dict[subject].keys():
                cond = pn.widgets.TextInput(value=condition)
                cond.link(
                    (subject, condition),
                    callbacks={"value": self.change_condition_name},
                )
                btn_remove_phase = pn.widgets.Button(
                    name="Remove Phase", button_type="danger"
                )
                btn_remove_phase.link(
                    (subject, condition),
                    callbacks={"value": self.remove_btn_click},
                )
                col.append(pn.Row(cond, btn_remove_phase))
                for phase, time in self.subject_time_dict[subject][condition].items():
                    row = pn.Row()
                    phase_name_input = pn.widgets.TextInput(value=phase)
                    phase_name_input.link(
                        (subject, condition, phase),
                        callbacks={"value": self.change_phase_name},
                    )
                    row.append(phase_name_input)
                    dt_picker = pn.widgets.DatetimePicker(value=time)
                    dt_picker.link(
                        (subject, condition, phase),
                        callbacks={"value": self.timestamp_changed},
                    )
                    row.append(dt_picker)
                    remove_btn = pn.widgets.Button(name="Remove", button_type="danger")
                    remove_btn.link(
                        (subject, condition, phase),
                        callbacks={"value": self.remove_btn_click},
                    )
                    row.append(remove_btn)
                    col.append(row)
                btn_subphase = pn.widgets.Button(
                    name="Add Subphase", button_type="primary"
                )
                btn_subphase.link(
                    (subject, condition),
                    callbacks={"value": self.add_subphase_btn_click},
                )
                row = pn.Row(pn.layout.HSpacer(), pn.layout.HSpacer(), btn_subphase)
                col.append(row)
            btn = pn.widgets.Button(name="Add Phase", button_type="primary")
            btn.link(
                (subject,),
                callbacks={"value": self.add_phase_btn_click},
            )
            col.append(btn)
            timestamps.append((subject, col))
        self.times.objects = [pn.Accordion(objects=timestamps)]

    def add_phase_btn_click(self, target, _):
        new_phase_name = "New Phase"
        self.subject_time_dict[target[0]][new_phase_name] = pd.Series(
            {"New Subphase": datetime.datetime.now()}
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

    def add_subphase_btn_click(self, target, event):
        new_phase_name = "New Subphase"
        if new_phase_name in list(
            self.subject_time_dict[target[0]][target[1]].index.values
        ):
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in list(
                self.subject_time_dict[target[0]][target[1]].index.values
            ):
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
        self.subject_time_dict[target[0]][target[1]] = pd.concat(
            [
                self.subject_time_dict[target[0]][target[1]],
                pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
            ]
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

    def get_outlier_params(self):
        if self.skip_outlier_detection:
            self.outlier_params = None
            self.selected_outlier_methods = None
            return None
        self.outlier_params = {
            "correlation": self.correlation.value,
            "quality": self.quality.value,
            "artifact": self.artifact.value,
            "statistical_rr": self.statistical_rr.value,
            "statistical_rr_diff": self.statistical_rr_diff.value,
            "physiological": (
                self.physiological_lower.value,
                self.physiological_upper.value,
            ),
        }
        return self.outlier_params

    @param.output(
        ("freq_bands", param.Dynamic),
        ("synced", param.Boolean),
        ("subject_time_dict", param.Dynamic),
        ("timezone", param.String()),
        ("trimmed_data", param.Dynamic),
        ("session", param.String),
        ("selected_signal", param.String),
        ("recording", param.String),
        ("data", param.Dynamic),
        ("sampling_rate", param.Number),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Boolean),
        ("time_log", param.Dynamic),
        ("outlier_params", param.Dynamic),
        ("selected_outlier_methods", param.Dynamic),
        ("skip_hrv", param.Boolean),
        ("subject", param.Dynamic),
        ("cft_sheets", param.Dynamic),
        ("phase_series", param.Dynamic),
    )
    def output(self):
        return (
            self.freq_bands,
            self.synced,
            self.subject_time_dict,
            self.timezone,
            self.trimmed_data,
            self.session,
            self.signal,
            self.recording,
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.get_outlier_params(),
            self.selected_outlier_methods,
            self.skip_hrv,
            self.subject,
            self.cft_sheets,
            self.phase_series,
        )


def delete_timezone_of_datetime_columns_(df):
    datetime_columns = get_datetime_columns_of_data_frame(df)
    for col in datetime_columns:
        df[col] = df[col].dt.tz_localize(None)
    return df


# noinspection PyUnusedLocal
class DownloadResults(PhysiologicalBase):
    load_plots_ecg = pn.widgets.Checkbox(name="Download ECG Plots")
    load_plots_eeg = pn.widgets.Checkbox(name="Download EEG Plots")
    load_plots_hrv = pn.widgets.Checkbox(name="HRV")
    load_plots_cft = pn.widgets.Checkbox(name="Download CFT Plots")
    load_plt_hr_ensemble = pn.widgets.Checkbox(name="HR Ensemble")
    zip_buffer = io.BytesIO()

    def __init__(self, **params):
        self.download_btn = None
        params["HEADER_TEXT"] = DOWNLOAD_RESULT_TEXT
        super().__init__(**params)
        self.update_step(12)
        self._load_results_checkbox = pn.widgets.Checkbox(name="Load Results")
        self._view = pn.Column(self.header)
        self._view.append(self._load_results_checkbox)
        self._view.append(self.load_plots_hrv)

    def get_selected_files(self):
        print("get selected files")
        pn.state.notifications.info("Loading Results")
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            if self.signal == "ECG":
                self.load_ecg_files(zip_file)
            elif self.signal == "EEG":
                self.load_eeg_files(zip_file)
            elif self.signal == "CFT":
                self.load_cft_files(zip_file)
        self.zip_buffer.seek(0)
        pn.state.notifications.info("Results loaded")
        return self.zip_buffer

    def load_eeg_files(self, zip_file):
        for key in self.eeg_processor.keys():
            df = self.eeg_processor[key].eeg_result["Data"]
            df = df.tz_localize(None)
            df.to_excel(f"eeg_result_{key}.xlsx", sheet_name=key)
            zip_file.write(f"eeg_result_{key}.xlsx")
        if self.load_plots_eeg.value:
            self.load_eeg_plots(zip_file)

    def load_cft_files(self, zip_file):
        for key in self.cft_processor.keys():
            df_cft = self.cft_processor[key]["CFT"]
            df_cft = df_cft.tz_localize(None)
            df_cft.to_excel(f"cft_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_{key}.xlsx")
            df_hr = self.cft_processor[key]["HR"]
            df_hr = df_hr.tz_localize(None)
            df_hr.to_excel(f"cft_hr_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_hr_{key}.xlsx")
            df_baseline = {
                "Baseline": [
                    self.cft_processor[key]["Baseline"],
                ]
            }
            df_baseline = pd.DataFrame.from_dict(df_baseline)
            df_baseline.to_excel(f"cft_baseline_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_baseline_{key}.xlsx")
            df_cft_parameters = self.cft_processor[key]["CFT Parameters"]
            df_cft_parameters = delete_timezone_of_datetime_columns_(df_cft_parameters)
            df_cft_parameters.to_excel(f"cft_parameters_{key}.xlsx", sheet_name=key)
            zip_file.write(f"cft_parameters_{key}.xlsx")
        if self.load_plots_cft.value:
            self.load_cft_plots(zip_file)

    def load_ecg_files(self, zip_file):
        if self.load_plots_ecg.value:
            self.load_ecg_plots(zip_file)
        if self.load_plots_hrv.value:
            self.load_hrv_plots(zip_file)
        if type(self.ecg_processor) != dict:
            if isinstance(self.ecg_processor.ecg_result, dict):
                for key in self.ecg_processor.ecg_result.keys():
                    df = self.ecg_processor.ecg_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"ecg_result.xlsx", sheet_name=key)
                    zip_file.write(f"ecg_result.xlsx")
            if isinstance(self.ecg_processor.hr_result, dict):
                for key in self.ecg_processor.hr_result.keys():
                    df = self.ecg_processor.hr_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"hr_result.xlsx")
                    zip_file.write(f"hr_result.xlsx")
            return
        for subject in self.ecg_processor.keys():
            if isinstance(self.ecg_processor[subject].ecg_result, dict):
                for key in self.ecg_processor[subject].ecg_result.keys():
                    df = self.ecg_processor[subject].ecg_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"ecg_result_{key}.xlsx", sheet_name=key)
                    zip_file.write(f"ecg_result_{key}.xlsx")
            if isinstance(self.ecg_processor[subject].hr_result, dict):
                for key in self.ecg_processor[subject].hr_result.keys():
                    df = self.ecg_processor[subject].hr_result[key]
                    df = df.tz_localize(None)
                    df.to_excel(f"hr_result_{key}.xlsx")
                    zip_file.write(f"hr_result_{key}.xlsx")

    def load_hrv_plots(self, zip_file):
        for key in self.ecg_processor.ecg_result.keys():
            buf = io.BytesIO()
            fig, axs = bp.signals.ecg.plotting.hrv_plot(self.ecg_processor, key=key)
            fig.savefig(buf)
            zip_file.writestr(f"HRV_{key}.png", buf.getvalue())

    def load_ecg_plots(self, zip_file):
        if self.subject is not None:
            for key in self.ecg_processor[self.subject].ecg_result.keys():
                buf = io.BytesIO()
                fig, axs = bp.signals.ecg.plotting.ecg_plot(
                    self.ecg_processor[self.subject], key=key
                )
                fig.savefig(buf)
                zip_file.writestr(f"ECG_{key}_{self.subject}.png", buf.getvalue())
        elif type(self.ecg_processor) != dict:
            buf = io.BytesIO()
            fig, axs = bp.signals.ecg.plotting.ecg_plot(self.ecg_processor, key="Data")
            fig.savefig(buf)
            zip_file.writestr(f"ECG.png", buf.getvalue())

    def load_eeg_plots(self, zip_file):
        for key in self.eeg_processor.keys():
            buf = io.BytesIO()
            palette = sns.color_palette(fau_colors.cmaps.faculties)
            sns.set_theme(
                context="notebook", style="ticks", font="sans-serif", palette=palette
            )
            fig, ax = plt.subplots(figsize=(10, 5))
            self.eeg_processor[key].eeg_result["Data"].plot(ax=ax)
            fig.savefig(buf)
            zip_file.writestr(f"ECG_{key}.png", buf.getvalue())

    def load_cft_plots(self, zip_file):
        palette = sns.color_palette(fau_colors.cmaps.faculties)
        sns.set_theme(
            context="notebook", style="ticks", font="sans-serif", palette=palette
        )
        cft = CFT()
        for key in self.cft_processor.keys():
            buf = io.BytesIO()
            fig, ax = plt.subplots(figsize=(10, 5))
            fig, _ = bp.signals.ecg.plotting.hr_plot(self.cft_processor[key]["HR"])
            fig.savefig(buf)
            zip_file.writestr(f"HR_{key}.png", buf.getvalue())
            fig, _ = cft.cft_plot(self.cft_processor[key]["HR"])
            buf = io.BytesIO()
            fig.savefig(buf)
            zip_file.writestr(f"CFT_{key}.png", buf.getvalue())

    def panel(self):
        self._load_results_checkbox.name = f"Load {self.signal} Results"
        if self.skip_hrv:
            self.load_plots_hrv.visible = False
        if self.download_btn is None:
            self.download_btn = pn.widgets.FileDownload(
                callback=self.get_selected_files, filename="Results.zip"
            )
            self._view.append(self.download_btn)
        else:
            self.download_btn.filename = "Results.zip"
        return self._view



class FrequencyBands(PhysiologicalBase):
    text = ""
    band_panel = pn.Column()
    freq_bands = {
        "theta": [4, 8],
        "alpha": [8, 13],
        "beta": [13, 30],
        "gamma": [30, 44],
    }

    def __init__(self, **params):
        params["HEADER_TEXT"] = SELECT_FREQUENCY_TEXT
        super().__init__(**params)
        self.update_step(9)
        pane = pn.Column(
            self.header,
            self.band_panel,
        )
        self._view = pane

    def show_freq_bands(self):
        pane = pn.Column()
        for key, value in self.freq_bands.items():
            remove_btn = pn.widgets.Button(name="Remove")
            remove_btn.link(
                (key),
                callbacks={"value": self.remove_band},
            )
            band_name_input = pn.widgets.TextInput(value=key)
            band_name_input.link(
                (key),
                callbacks={"value": self.change_band_name},
            )
            band_freq_input = pn.widgets.ArrayInput(value=np.array(value))
            band_freq_input.link(
                (key),
                callbacks={"value": self.change_freq_bands},
            )
            pane.append(
                pn.Row(
                    band_name_input,
                    band_freq_input,
                    remove_btn,
                )
            )
        add_band = pn.widgets.Button(name="Add", button_type="primary")
        add_band.link(
            None,
            callbacks={"value": self.add_band},
        )
        pane.append(pn.Row(add_band))
        self.band_panel.objects = [pane]

    def change_freq_bands(self, key, target):
        if len(target.new) == 2:
            self.freq_bands[key] = list(target.new)
        self.show_freq_bands()

    def change_band_name(self, key, target):
        self.freq_bands[target.new] = self.freq_bands.pop(key)
        self.show_freq_bands()

    def change_phase_name(self, target, event):
        self.subject_time_dict[target[0]][target[1]].rename(
            {target[2]: event.new}, inplace=True
        )
        self.dict_to_column()

    def remove_band(self, key, target):
        self.freq_bands.pop(key)
        self.show_freq_bands()

    def add_band(self, _, target):
        new_name = "new"
        i = 0
        while new_name in self.freq_bands.keys():
            i += 1
            new_name = "new " + str(i)
        self.freq_bands[new_name] = [0, 0]
        self.show_freq_bands()

    def panel(self):
        return self._view



class SetRspParameters(PhysiologicalBase):
    checkbox_estimate_rsp = pn.widgets.Checkbox(name="Estimate RSP", value=False)
    select_estimation_method = pn.widgets.Select(
        name="Estimation Method",
        options=EDR_TYPES,
        visible=False,
        sizing_mode="stretch_width",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SET_RSP_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.checkbox_estimate_rsp.link(
            self.select_estimation_method,
            callbacks={"value": self.checkbox_estimate_changed},
        )
        self.select_estimation_method.link(
            self, callbacks={"value": self.change_estimation_method}
        )
        self._view = pn.Column(
            self.header, self.checkbox_estimate_rsp, self.select_estimation_method
        )

    def change_estimation_method(self, _, event):
        self.estimate_rsp_method = event.new

    def checkbox_estimate_changed(self, _, event):
        self.select_estimation_method.visible = event.new
        self.estimate_rsp = event.new

    def panel(self):
        return self._view



class SelectCFTSheet(PhysiologicalBase):
    select_cft_sheets = pn.widgets.CheckBoxGroup(
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = SELECT_CFT_TEXT
        super().__init__(**params)
        self.step = 6
        self.update_step(self.step)
        self.update_text(SELECT_CFT_TEXT)
        self.select_cft_sheets.link(self, callbacks={"value": self.sheet_checked})
        pane = pn.Column(self.header)
        pane.append(self.select_cft_sheets)
        self._view = pane

    def sheet_checked(self, _, event):
        if len(self.select_cft_sheets.value) == 0:
            self.ready = False
            self.cft_sheets = []
        else:
            self.ready = True
            self.cft_sheets = self.select_cft_sheets.value

    def panel(self):
        self.select_cft_sheets.options = list(self.data.keys())
        return self._view



class Session(PhysiologicalBase):
    select_session = pn.widgets.Select(
        name="",
        value="Single Session",
        options=["Multiple Sessions", "Single Session"],
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = SESSION_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.select_session.link(self, callbacks={"value": self.signal_selected})
        self.update_text(SESSION_TEXT)
        pane = pn.Column(
            self.header,
            self.select_session,
        )
        self._view = pane

    def signal_selected(self, _, event):
        self.session = event.new
        self.ready = self.session != ""

    def panel(self):
        return self._view



class Recordings(PhysiologicalBase):
    select_recording = pn.widgets.Select(
        options=["Multiple Recording", "Single Recording"],
        name="Select recording type",
        value="Single Recording",
        sizing_mode="stretch_width",
    )
    next = param.Selector(
        default="Upload Files", objects=["Upload Files", "Multiple Files"]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = RECORDINGS_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.select_recording.link(self, callbacks={"value": self.chg})
        self._view = pn.Column(
            self.header,
            self.select_recording,
        )

    def chg(self, _, event):
        self.recording = event.new
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        return self._view



class Compress(PhysiologicalBase):
    def __init__(self, **params):
        params["HEADER_TEXT"] = COMPRESS_FILES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self._view = pn.Column(
            self.header,
        )

    def panel(self):
        return self._view
from datetime import datetime
from io import StringIO
from biopsykit.io.io import (
    _sanitize_index_cols,
)



class AskToAddTimes(PhysiologicalBase):
    ready = param.Boolean(default=False)
    next = param.Selector(
        default="Add Times",
        objects=["Do you want to detect Outlier?", "Add Times", "Frequency Bands"],
    )
    skip_btn = pn.widgets.Button(
        name="Skip", button_type="default", sizing_mode="stretch_width"
    )
    add_times_btn = pn.widgets.Button(
        name="Add Phases", button_type="primary", sizing_mode="stretch_width"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_ADD_TIMES_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.add_times_btn.link(self, callbacks={"clicks": self.click_add_times})
        self.ready = False
        pane = pn.Column(self.header)
        pane.append(pn.Row(self.add_times_btn, self.skip_btn))
        self._view = pane

    def click_skip(self, _, event):
        if self.signal == "EEG":
            self.next = "Frequency Bands"
            self.ready = True
        else:
            self.next = "Do you want to detect Outlier?"
            self.ready = True

    def click_add_times(self, _, event):
        self.next = "Add Times"
        self.ready = True

    def panel(self):
        return self._view


class AddTimes(PhysiologicalBase):
    time_upload = pn.widgets.FileInput(
        styles={"background": "whitesmoke"}, multiple=False, accept=".xls,.xlsx,.csv"
    )
    datetime = [
        (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.now()),
        )
    ]
    add_button = pn.widgets.Button(name="Add timestamp", button_type="danger")
    remove_button = pn.widgets.Button(name="Remove last Phase", button_type="danger")
    pane = pn.Column()
    subject_log = None
    subject_timestamps = []
    df = None
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )
    next = param.Selector(
        default="Do you want to detect Outlier?",
        objects=["Do you want to detect Outlier?", "Frequency Bands"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ADD_TIMES_TEXT
        self.ready = False
        super().__init__(**params)
        self.update_step(6)
        self.time_upload.link(self, callbacks={"value": self.parse_time_file})
        self.times = pn.Column(
            self.datetime[0][0], self.datetime[0][1], self.add_button
        )
        self.times_to_subject = TimesToSubject([])
        self.select_subject = pn.widgets.Select(
            name="Select Subject column", visible=False
        )
        self.select_condition = pn.widgets.Select(
            name="Select Condition column", visible=False
        )
        self.select_condition.visible = True
        self.select_condition.link(
            self,
            callbacks={"value": self.condition_column_changed},
        )
        self.select_subject.link(
            self,
            callbacks={"value": self.subject_column_changed},
        )
        pane = pn.Column(self.header)
        pane.append(
            pn.Row(
                pn.widgets.StaticText(
                    name="Add Times",
                    value="Here you can add Time sections manually or you can upload an Excel File",
                )
            )
        )
        pane.append(
            pn.Row(
                self.time_upload,
                self.times_to_subject,
            )
        )
        pane.append(pn.Row(self.select_vp))
        pane.append(pn.Row(self.select_subject, self.select_condition))
        self.ready = self.times_to_subject.is_ready()
        self._view = pane

    def panel(self):
        if self.signal == "EEG":
            self.next = "Frequency Bands"
        self.times_to_subject.initialize_filenames(list(self.data.keys()))
        return self._view

    def parse_time_file(self, target, event):
        self.select_condition.visible = False
        self.select_subject.visible = False
        self.select_vp.visible = False
        self.df = self.parse_file(self.time_upload.filename, self.time_upload.value)
        if self.df is None:
            pn.state.notifications.error("Could not parse the given time File")
            return
        if not self.ready:
            self.ask_for_additional_infos()
            return
        self.set_subject_time_dict()

    def ask_for_additional_infos(self):
        row = pn.Row()
        cols = list(self.df.columns)
        cols.insert(0, " ")
        if "subject" not in self.df.columns:
            self.select_subject.options = cols
            self.select_subject.visible = True
        if "condition" not in self.df.columns:
            self.select_condition.options = cols
            self.select_condition.visible = True
        self.pane.append(row)

    def parse_file(self, file_name, file_content) -> pd.DataFrame:
        if file_content is None:
            pn.state.notifications.error("No file content")
            return pd.DataFrame()
        if ".csv" in file_name:
            string_io = StringIO(file_content.decode("utf8"))
            df = pd.read_csv(string_io)
        else:
            df = pd.read_excel(file_content)
        df = self.handle_time_file(df)
        return df

    def select_vp_changed(self, _, event):
        self.subject = event.new

    def set_subject_time_dict(self):
        for subject_name in self.df.index:
            conditions = self.df.loc[subject_name]
            cond_name = conditions.condition
            t_condition = conditions.drop(labels=["condition"])
            t_condition = t_condition.apply(
                lambda time: datetime.combine(
                    datetime.now().date(),
                    time,
                )
                if not isinstance(time, datetime)
                else time
            )
            self.subject_time_dict[subject_name] = {}
            self.subject_time_dict[subject_name][cond_name] = t_condition
        self.times_to_subject.add_new_subject_time_dict(self.subject_time_dict)

    def check_subject_condition_columns(self, df):
        if "subject" not in df.columns:
            pn.state.notifications.error("Subject column must be specified")
            return False
        if "condition" not in df.columns:
            pn.state.notifications.error("Condition column must be specified")
            return False
        return True

    def subject_column_changed(self, _, event):
        col = event.new
        if col == " ":
            return
        col_name = "subject"
        self.df = self.df.rename(columns={col: col_name})
        if not self.check_subject_condition_columns(self.df):
            return
        self.ready = True
        self.df = self.handle_time_file(self.df)
        self.set_subject_time_dict()
        self.select_subject.visible = False

    def condition_column_changed(self, _, event):
        col = event.new
        if col == " ":
            return
        col_name = "condition"
        self.df = self.df.rename(columns={col: col_name})
        if not self.check_subject_condition_columns(self.df):
            return
        self.ready = True
        self.df = self.handle_time_file(self.df)
        self.set_subject_time_dict()
        self.select_condition.visible = False

    def handle_time_file(self, df):
        if not self.check_subject_condition_columns(df):
            self.ready = False
            return df
        subject_col = "subject"
        condition_col = "condition"
        if self.session == "Single Session":
            df, index_cols = _sanitize_index_cols(
                data=df,
                subject_col=subject_col,
                condition_col=condition_col,
                additional_index_cols=None,
            )
            df = df.set_index(subject_col)
            self.ready = True
            return df
        else:
            df = df.set_index(subject_col)
            self.ready = True
            return df

    def init_subject_time_dict(self):
        if type(self.data) != dict:
            return
        for subject in self.data.keys():
            self.subject_time_dict[subject] = {}
            if self.session == "Single Session":
                continue
            for condition in self.data[subject].keys():
                self.subject_time_dict[subject][condition] = pd.Series(
                    dtype="datetime64[ns]"
                )

    @param.output(
        ("freq_bands", param.Dynamic),
        ("synced", param.Boolean),
        ("subject_time_dict", param.Dynamic),
        ("timezone", param.String()),
        ("trimmed_data", param.Dynamic),
        ("session", param.String),
        ("selected_signal", param.String),
        ("recordings", param.String),
        ("recording", param.String),
        ("data", param.Dynamic),
        ("sampling_rate", param.Number),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Boolean),
        ("time_log", param.Dynamic),
        ("outlier_params", param.Dynamic),
        ("selected_outlier_methods", param.Dynamic),
        ("skip_hrv", param.Boolean),
        ("subject", param.Dynamic),
        ("cft_sheets", param.Dynamic),
        ("phase_series", param.Dynamic),
    )
    def output(self):
        file_dict = self.times_to_subject.get_files_to_subjects()
        subject_time_dict = self.times_to_subject.get_subject_time_dict()
        for file_name in file_dict.keys():
            self.data[file_dict[file_name]] = self.data.pop(file_name)
        self.subject_time_dict = subject_time_dict
        return (
            self.freq_bands,
            self.synced,
            self.subject_time_dict,
            self.timezone,
            self.trimmed_data,
            self.session,
            self.signal,
            self.recordings,
            self.recording,
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.get_outlier_params(),
            self.selected_outlier_methods,
            self.skip_hrv,
            self.subject,
            self.cft_sheets,
            self.phase_series,
        )
from typing import Tuple, List, Dict
from zipfile import ZipFile
from biopsykit.io.eeg import MuseDataset
from io import BytesIO
from io import StringIO
from nilspodlib import SyncedSession, Dataset


class FileUpload(PhysiologicalBase):
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xlsx",
        sizing_mode="stretch_width",
    )
    select_timezone = pn.widgets.Select(
        options=["None Selected"] + list(pytz.all_timezones),
        value="Europe/Berlin",
        name="Timezone",
        sizing_mode="stretch_width",
    )
    select_hardware = pn.widgets.Select(
        options=["NilsPod", "BioPac"],
        value="NilsPod",
        name="Hardware",
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = FILE_UPLOAD_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.select_timezone.link(self, callbacks={"value": self.timezone_changed})
        self.select_hardware.link(self, callbacks={"value": self.hardware_changed})
        self._select_hardware = pn.widgets.Select.from_param(self.param.hardware)
        pn.bind(self.hardware_changed, self._select_hardware.value, watch=True)
        pn.bind(self.parse_file_input, self.file_input.param.value, watch=True)
        self._view = pn.Column(
            self.header,
            self.select_hardware,
            self.select_timezone,
            self.file_input,
        )

    def timezone_changed(self, _, event):
        self.timezone = event.new
        if self.timezone == "None Selected":
            self.ready = False
        else:
            self.ready = True

    def hardware_changed(self, _, event):
        self.hardware = event.new
        if self.hardware == "NilsPod":
            self.file_input.accept = ".csv,.bin, .zip"
        if self.hardware == "BioPac":
            self.file_input.accept = ".acq"

    def parse_file_input(self, _):
        self.ready = self.data is not None
        self.data = None
        if self.file_input.value is None or len(self.file_input.value) <= 0:
            pn.state.notifications.error("No Files arrived")
            return
        if self.file_input.filename is None or "." not in self.file_input.filename:
            pn.state.notifications.error("No Files arrived")
            return
        fileType = self.file_input.filename[self.file_input.filename.rindex(".") + 1 :]
        try:
            match fileType:
                case "zip":
                    self.handle_zip_file(self.file_input.value)
                case "csv":
                    self.handle_csv_file(
                        file_name=self.file_input.name,
                        file_content=self.file_input.value,
                    )
                case "bin":
                    self.handle_bin_file(
                        file_name=self.file_input.filename,
                        file_content=self.file_input.value,
                    )
                case "xlsx":
                    self.handle_xlsx_file(
                        file_content=self.file_input.value,
                        filename=self.file_input.filename,
                    )
                case _:
                    pn.state.notifications.error("No matching parser found")
                    self.ready = False
                    return
            if self.ready:
                pn.state.notifications.success(
                    "File uploaded successfully", duration=5000
                )
            else:
                pn.state.notifications.error("File upload failed", duration=5000)
        except Exception as e:
            self.ready = False
            pn.state.notifications.error(f"File upload failed: {str(e)}", duration=5000)

    def handle_zip_file(self, input_zip: bytes):
        datasets, subject_data_dict = self.extract_zip(input_zip)
        if datasets is None or subject_data_dict is None:
            self.ready = False
            return
        try:
            subject_synced = {}
            sampling_rates = []
            for subject in subject_data_dict.keys():
                fs, df = self.sync_session(datasets=subject_data_dict[subject])
                subject_synced[subject] = df
                sampling_rates.append(fs)
            self.data = subject_synced
            self.sampling_rate = sampling_rates[0]
            self.ready = True
        except Exception:
            subject_phase_data_dict = {}
            for subject in subject_data_dict.keys():
                dataset_list = [
                    bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
                    for dataset in subject_data_dict[subject]
                ]
                fs_list = [fs for df, fs in dataset_list]
                df_all = pd.concat([df for df, fs in dataset_list], axis=0)
                self.sampling_rate = fs_list[0]
                subject_phase_data_dict[subject] = df_all
            self.data = subject_phase_data_dict
            self.ready = True

    @staticmethod
    def sync_session(datasets: List[Dataset]) -> Tuple[float, pd.DataFrame]:
        for dataset in datasets:
            _handle_counter_inconsistencies_dataset(dataset, "ignore")
        synced = SyncedSession(datasets)
        synced.align_to_syncregion(inplace=True)
        df = synced.data_as_df(None, index="local_datetime", concat_df=True)
        df.index.name = "time"
        if len(set(synced.info.sampling_rate_hz)) > 1:
            raise ValueError()
        fs = synced.info.sampling_rate_hz[0]
        return fs, df

    def extract_zip(
        self, input_zip: bytes
    ) -> Tuple[List[Dataset], Dict[str, List[Dataset]]]:
        input_zip = ZipFile(BytesIO(input_zip))
        datasets = []
        subject_data_dict = {}
        for file in input_zip.infolist():
            if file.filename.startswith("__"):
                continue
            if ".bin" in file.filename:
                dataset, subject_id = self.read_zipped_bin_file(file, input_zip)
                datasets.append(dataset)
                if subject_id in subject_data_dict.keys():
                    subject_data_dict[subject_id].append(dataset)
                else:
                    subject_data_dict[subject_id] = [dataset]
        return datasets, subject_data_dict

    def read_zipped_bin_file(
        self, file: zipfile.ZipInfo, input_zip: ZipFile
    ) -> Tuple[Dataset, str]:
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=BytesIO(input_zip.read(file.filename)),
            legacy_support="resolve",
            tz=self.timezone,
        )
        subject_id = self.extract_subject_id(file.filename)
        return dataset, subject_id

    @staticmethod
    def extract_subject_id(filename: str) -> str:
        if "/" not in filename and "_" not in filename:
            Exception("The archive has the wrong structure")
        if "/" not in filename:
            return filename.split(".")[0].split("_")[-1]
        filenames = filename.split("/")
        if len(filenames) > 3 or len(filenames) < 2:
            Exception("The archive has the wrong structure")
        elif len(filenames) == 2 and "_" in filenames[1] and "." in filenames[1]:
            return filenames[1].split(".")[0].split("_")[-1]
        elif len(filenames) == 3:
            return filenames[1]
        else:
            Exception("The archive has the wrong structure")

    def handle_csv_file(self, file_name: string, file_content: bytes):
        string_io = StringIO(file_content.decode("utf8"))
        df = pd.read_csv(string_io)
        if self.signal == "EEG":
            muse = MuseDataset(data=df, tz=self.timezone)
            df = muse.data_as_df("local_datetime")
            self.sampling_rate = muse.sampling_rate_hz
            self.data = {file_name: df}
        else:
            self.data = {file_name: self.convert_columns(df)}
        if self.data is None or len(self.data) == 0:
            Exception("No data found in file")
        self.ready = True

    @staticmethod
    def convert_columns(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if "timestamp" in col.lower():
                try:
                    df[col] = pd.Timestamp(df[col])
                    df.set_index(col, inplace=True)
                except ValueError:
                    pass
            elif "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                except ValueError:
                    pass
        return df

    def handle_bin_file(self, file_name: string, file_content: bytes):
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=BytesIO(file_content),
            tz=self.timezone,
        )
        self.sensors = set(dataset.info.enabled_sensors)
        df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
        self.sampling_rate = fs
        self.data = {file_name: df}
        self.ready = True

    def handle_xlsx_file(self, file_content: bytes, filename: string):
        if self.signal == "CFT":
            dict_hr = pd.read_excel(
                BytesIO(file_content), index_col="time", sheet_name=None
            )
            dict_hr = {k: v.tz_localize(self.timezone) for k, v in dict_hr.items()}
            self.data[filename] = dict_hr
        if "hr_result" in filename:
            subject_id = re.findall("hr_result_(Vp\w+).xlsx", filename)[0]
            hr = pd.read_excel(BytesIO(file_content), sheet_name=None, index_col="time")
            self.hr_data[subject_id] = hr
        self.ready = True

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone)

    def panel(self):
        self.ready = self.data is not None
        if self.recording == "Multiple Recording":
            self.file_input.accept = ".zip"
        else:
            self.file_input.accept = ".csv,.bin,.xlsx"
        return self._view




class DataArrived(PhysiologicalBase):
    ready = param.Boolean(default=False)
    subject_selector = pn.widgets.Select(
        sizing_mode="stretch_width",
    )
    sampling_rate_input = pn.widgets.TextInput(
        name="Sampling rate Input",
        placeholder="Enter your sampling rate here...",
        sizing_mode="stretch_width",
    )
    info_selected_value = pn.pane.Str("")
    next = param.Selector(
        objects=["Do you want to add time logs?", "Select CFT Sheet", "Data arrived"],
        default="Do you want to add time logs?",
    )
    data_view = pn.widgets.Tabulator(
        pagination="local",
        layout="fit_data_stretch",
        page_size=20,
        header_align="right",
        visible=False,
        disabled=True,
        sizing_mode="stretch_width",
    )
    session_start = pn.widgets.DatetimePicker(
        name="Session start:", disabled=True, sizing_mode="stretch_width", visible=False
    )
    session_end = pn.widgets.DatetimePicker(
        name="Session end:",
        disabled=True,
        sizing_mode="stretch_width",
        visible=False,
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = DATA_ARRIVED_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.sampling_rate_input.link(
            self, callbacks={"value": self.set_sampling_rate_value}
        )
        self.subject_selector.link(self, callbacks={"value": self.subject_selected})
        self._view = pn.Column(
            self.header,
            self.subject_selector,
            self.sampling_rate_input,
            self.session_start,
            self.session_end,
            self.data_view,
        )

    def set_sampling_rate_value(self, _, event):
        self.sampling_rate = self.convert_str_to_float(event.new)
        if self.sampling_rate > 0:
            self.ready = True
        else:
            pn.state.notifications.error(
                "Sampling rate must be a number (seperated by a .)"
            )
            self.ready = False

    @staticmethod
    def convert_str_to_float(str_value: str) -> float:
        try:
            float_value = float(str_value)
            if math.isnan(float_value):
                return -1.0
            return float_value
        except ValueError:
            return -1.0

    def subject_selected(self, _, event):
        if not event.new:
            self.session_end.visible = False
            self.session_start.visible = False
            self.data_view.visible = False
            return
        if self.data is None:
            self.session_end.visible = False
            self.session_start.visible = False
            self.data_view.visible = False
            return
        if isinstance(self.data[event.new], pd.DataFrame):
            self.data_view.value = self.data[event.new]
            self.data_view.visible = True
        self.set_session_start_and_end()

    def set_session_start_and_end(self):
        if (
            self.subject_selector.value is None
            or self.subject_selector.value == ""
            or self.data is None
            or self.subject_selector.value not in list(self.data.keys())
        ):
            return
        if isinstance(self.data[self.subject_selector.value], pd.DataFrame):
            ds = self.data[self.subject_selector.value]
            self.session_start.value = ds.index[0]
            self.session_end.value = ds.index[-1]
        elif isinstance(self.data[self.subject_selector.value], nilspodlib.Dataset):
            ds = self.data[self.subject_selector.value]
            self.session_start.value = ds.start_time
            self.session_end.value = ds.end_time
        self.session_start.visible = True
        self.session_end.visible = True

    def panel(self):
        if self.signal == "CFT":
            self.next = "Select CFT Sheet"
        elif self.signal == "RSP":
            self.next = "Set RSP Parameters"
        else:
            self.next = "Do you want to add time logs?"
        if self.sampling_rate > 0:
            self.sampling_rate_input.value = str(self.sampling_rate)
            self.ready = True
        else:
            self.sampling_rate_input.value = ""
            self.ready = False
            pn.state.notifications.warning("Please provide a sampling rate")
        self.subject_selector.options = [""] + list(self.data.keys())
        self.subject_selector.value = ""
        self.subject_selector.visible = self.data is not None
        self.data_view.visible = self.data is not None
        return self._view



class AskToDetectOutliers(PhysiologicalBase):
    next = param.Selector(
        default="Do you want to process the HRV also?",
        objects=["Do you want to process the HRV also?", "Expert Outlier Detection"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(
        name="Skip", sizing_mode="stretch_width", button_type="default"
    )
    expert_mode_btn = pn.widgets.Button(
        name="Expert Mode", button_type="danger", sizing_mode="stretch_width"
    )
    default_btn = pn.widgets.Button(
        name="Default", button_type="primary", sizing_mode="stretch_width"
    )
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=OUTLIER_METHODS
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_DETECT_OUTLIER_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_detect_outlier})
        self.default_btn.link(self, callbacks={"clicks": self.click_default})
        self._view = pn.Column(
            self.header,
            pn.Row(self.default_btn, self.expert_mode_btn, self.skip_btn),
        )

    def click_skip(self, target, event):
        self.next = "Do you want to process the HRV also?"
        self.skip_outlier_detection = True
        self.ready = True

    def click_detect_outlier(self, target, event):
        self.next = "Expert Outlier Detection"
        self.skip_outlier_detection = False
        self.ready = True

    def click_default(self, target, event):
        self.next = "Do you want to process the HRV also?"
        self.skip_outlier_detection = False
        self.ready = True

    def panel(self):
        return self._view


class OutlierDetection(PhysiologicalBase):
    textHeader = ""
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=OUTLIER_METHODS
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = OUTLIER_DETECTION_TEXT
        super().__init__(**params)
        self.step = 6
        self.update_step(6)
        self.update_text(OUTLIER_DETECTION_TEXT)
        self.set_progress_value(self.step)
        self.physiological_upper.link(self, callbacks={"value": self.check_upper_bound})
        self.physiological_lower.link(self, callbacks={"value": self.check_lower_bound})
        self.outlier_methods.link(
            self, callbacks={"value": self.outlier_methods_changed}
        )
        pane = pn.Column(self.header)
        pane.append(
            pn.Column(
                self.outlier_methods,
                self.correlation,
                self.quality,
                self.artifact,
                self.statistical_rr,
                self.statistical_rr_diff,
                pn.Row(self.physiological_lower, self.physiological_upper),
            )
        )
        self._view = pane

    def outlier_methods_changed(self, _, event):
        if len(event.new) == 0:
            self.selected_outlier_methods = None
        self.selected_outlier_methods = event.new

    def check_upper_bound(self, target, event):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            switched_value = self.physiological_lower.value
            self.physiological_lower.value = self.physiological_upper.value
            self.physiological_upper.value = switched_value

    def check_lower_bound(self, target, event):
        if self.physiological_lower.value < 0:
            self.physiological_lower.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            switched_value = self.physiological_upper.value
            self.physiological_upper.value = self.physiological_lower.value
            self.physiological_lower.value = switched_value

    def panel(self):
        return self._view
from biopsykit.protocols import CFT
from biopsykit.signals.ecg import EcgProcessor
from biopsykit.signals.eeg import EegProcessor
from biopsykit.signals.rsp import RspProcessor
from nilspodlib import Dataset



class ProcessingPreStep(PhysiologicalBase):
    ready = param.Boolean(default=False)
    ready_btn = pn.widgets.Button(name="Ok", button_type="primary")

    def __init__(self, **params):
        params["HEADER_TEXT"] = PRESTEP_PROCESSING_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.ready_btn.link(self, callbacks={"clicks": self.ready_btn_click})
        self._view = pn.Column(self.header, self.ready_btn)

    def ready_btn_click(self, target, event):
        self.ready = True

    def panel(self):
        return self._view


class ProcessingAndPreview(PhysiologicalBase):
    phase_title = pn.widgets.StaticText(name="Phase", visible=False)
    results = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = PROCESSING_PREVIEW_TEXT
        super().__init__(**params)
        self.update_step(9)
        self.subject_time_dict = {}
        self.result_view = SubjectDataFrameView({})
        self.result_graph = PlotViewer(None, None, None)
        self._view = pn.Column(
            self.header, self.results, self.result_view, self.result_graph
        )

    def get_phases(self) -> list:
        if self.subject is not None:
            return self.ecg_processor[self.subject].phases
        if type(self.ecg_processor) != dict:
            return self.ecg_processor.phases
        keys = list(self.ecg_processor.keys())
        if len(keys) == 1:
            return self.ecg_processor[keys[0]].phases
        elif len(keys) > 1:
            return keys
        return ["data"]

    def processing(self):
        col = pn.Column()
        if self.signal == "ECG":
            col = self.process_ecg()
        elif self.signal == "EEG":
            col = self.process_eeg()
        elif self.signal == "RSP":
            self.process_rsp()
        if not self.skip_hrv:
            col.append(self.process_hrv())
        return col

    def get_dataframes_as_accordions(self):
        accordion = pn.Accordion()
        df = self.data
        if type(self.data) == Dataset:
            df = self.data.data_as_df()
        if type(self.data) == dict:
            df = {}
            for key in self.data.keys():
                df[key] = self.data[key]
        if self.data_processed:
            return accordion
        return accordion

    def process_rsp(self):
        if self.sampling_rate == -1:
            pn.state.notifications.error("Bitte eine sampling Rate eingeben")
            return
        if self.estimate_rsp:
            self.rsp_processor = {}
            for subject in self.data.keys():
                time_intervals = self.get_timelog(subject)
                ep = EcgProcessor(
                    data=self.data[subject],
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_intervals,
                )
                ep.ecg_process(
                    outlier_correction=self.selected_outlier_methods,
                    outlier_params=self.outlier_params,
                )
                phases = (
                    list(time_intervals.keys())
                    if time_intervals is not None
                    else ["Data"]
                )
                for phase in phases:
                    rsp_signal = ep.ecg_estimate_rsp(
                        ep, key=phase, edr_type=self.estimate_rsp_method
                    )
                    rsp_rate = RspProcessor.rsp_compute_rate(
                        rsp_signal, sampling_rate=self.sampling_rate
                    )
                    self.rsp_processor[subject] = {phase: (rsp_signal, rsp_rate)}
        else:
            self.rsp_processor = {}
            for subject in self.data.keys():
                time_intervals = self.get_timelog(subject)
                rp = RspProcessor(
                    data=self.data[subject],
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_intervals,
                )
                rsp_rate = rp.rsp_compute_rate(
                    self.data[subject], sampling_rate=self.sampling_rate
                )
                self.rsp_processor[subject] = {"Data": (self.data[subject], rsp_rate)}
        self.data_processed = True

    def process_cft(self):
        cft = CFT()
        col = pn.Column()
        for sheet in self.cft_sheets:
            df_hr = self.data[sheet]
            df_cft = cft.extract_cft_interval(self.data[sheet])
            self.cft_processor[sheet] = {
                "Baseline": cft.baseline_hr(df_hr),
                "CFT": df_cft,
                "CFT Parameters": cft.compute_cft_parameter(df_hr),
                "HR": df_hr,
            }
            hr_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
            fig, _ = bp.signals.ecg.plotting.hr_plot(df_hr)
            hr_plot.object = fig
            cft_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
            fig, _ = cft.cft_plot(data=df_hr)
            cft_plot.object = fig
            col.append("## " + sheet)
            col.append(pn.layout.Divider())
            col.append(hr_plot)
            col.append(cft_plot)
        return col

    def get_timelog(self, subject: str):
        time_log = self.subject_time_dict
        if not bool(time_log):
            return None
        if self.session == "Single Session":
            time_log = self.subject_time_dict[subject]
            for key in time_log.keys():
                time_log[key] = time_log[key].apply(lambda dt: dt.time())
            time_log = time_log[list(time_log.keys())[0]]
        return time_log

    def process_eeg(self):
        col = pn.Column()
        if self.sampling_rate == -1:
            pn.state.notifications.error("Bitte eine sampling Rate eingeben")
            return
        for subject in list(self.data.keys()):
            time_intervals = (
                self.get_timelog(subject) if self.subject_time_dict else None
            )
            self.eeg_processor[subject] = EegProcessor(
                data=self.data[subject],
                sampling_rate=float(self.sampling_rate),
                time_intervals=time_intervals,
            )
            self.eeg_processor[subject].relative_band_energy(
                freq_bands=self.freq_bands, title=subject
            )
        self.data_processed = True
        return col

    def process_ecg(self):
        col = pn.Column()
        self.ecg_processor = {}
        for subject in self.data.keys():
            ep = EcgProcessor(
                data=self.data[subject],
                sampling_rate=self.sampling_rate,
                time_intervals=self.get_timelog(subject),
            )
            ep.ecg_process(
                outlier_correction=self.selected_outlier_methods,
                outlier_params=self.outlier_params,
            )
            self.ecg_processor[subject] = ep
        # elif self.session == "Multiple Sessions":
        #     self.ecg_processor = {}
        #     for subject in self.data.keys():
        #         ep = EcgProcessor(
        #             data=self.data[subject],
        #             sampling_rate=self.sampling_rate,
        #             time_intervals=self.get_timelog(subject),
        #         )
        #         ep.ecg_process(
        #             outlier_correction=self.selected_outlier_methods,
        #             outlier_params=self.outlier_params,
        #             title=subject,
        #         )
        #         self.ecg_processor[subject] = ep
        subject_result_dict = {}
        graph_dict = {}
        for subject in self.ecg_processor.keys():
            subject_result_dict[subject] = {
                "ECG Result": self.ecg_processor[subject].ecg_result,
                "Heart Rate Result": self.ecg_processor[subject].heart_rate,
                "HRV Result": self.ecg_processor[subject].hr_result,
            }
            graph_dict[subject] = self.ecg_processor[subject]
        self.result_view.set_subject_results(subject_result_dict)
        self.result_graph.set_signal(graph_dict)
        return col

    def process_hr(self):
        if self.hr_data is None:
            return
        dict_result = bp.utils.data_processing.resample_dict_sec(self.hr_data)
        dict_result_norm = bp.utils.data_processing.normalize_to_phase(
            dict_result, "Baseline"
        )
        dict_result_norm_selected = bp.utils.data_processing.select_dict_phases(
            dict_result_norm, phases=["Intervention", "Stress", "Recovery"]
        )
        dict_study = bp.utils.data_processing.rearrange_subject_data_dict(
            dict_result_norm
        )
        dict_result = bp.utils.data_processing.cut_phases_to_shortest(dict_study)
        dict_merged = bp.utils.data_processing.merge_study_data_dict(dict_result)
        # TODO: Condition List bekommen wir im TimeLog
        # dict_merged_cond = bp.utils.data_processing.split_subject_conditions(dict_merged, condition_list)

    def get_statistical_values(self):
        values = []
        if type(self.ecg_processor) != dict:
            for column in self.ecg_processor.ecg_result:
                if not "Rate" in column:
                    continue
                df = self.ecg_processor.ecg_result[column]
                fig = px.box(df, y=column)
                plotly_pane = pn.pane.Plotly(fig)
                values.append(("Boxplot  : " + column, plotly_pane))
        else:
            for subject in self.ecg_processor.keys():
                for column in self.ecg_processor[subject].ecg_result:
                    if not "Rate" in column:
                        continue
                    df = self.ecg_processor[subject].ecg_result[column]
                    fig = px.box(df, y=column)
                    plotly_pane = pn.pane.Plotly(fig)
                    values.append(("Boxplot " + subject + ": " + column, plotly_pane))
        return values

    def phase_changed(self, target, event):
        if self.subject is not None:
            fig, axs = bp.signals.ecg.plotting.ecg_plot(
                self.ecg_processor[self.subject], key=event.new
            )
            target.object = fig
            self.phase_title.value = event.new

    def process_hrv(self):
        if self.skip_hrv:
            return
        for subject in list(self.ecg_processor.keys()):
            self.dict_hr_subjects[subject] = {}
            for key in self.ecg_processor[subject].ecg_result.keys():
                self.dict_hr_subjects[subject][key] = self.ecg_processor[
                    subject
                ].hrv_process(
                    self.ecg_processor[subject],
                    key,
                    index=subject,
                    hrv_types=self.hrv_types.value,
                    correct_rpeaks=self.correct_rpeaks.value,
                )

    def panel(self):
        self.results = self.processing()
        self.result_graph.set_signal_type(self.signal)
        self.result_graph.set_sampling_rate(self.sampling_rate)
        return self._view



class AskToProcessHRV(PhysiologicalBase):
    methods = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]
    skip_btn = pn.widgets.Button(name="Skip", sizing_mode="stretch_width")
    expert_mode_btn = pn.widgets.Button(
        name="Expert Mode", button_type="warning", sizing_mode="stretch_width"
    )
    default_btn = pn.widgets.Button(
        name="Default", button_type="primary", sizing_mode="stretch_width"
    )
    next_page = param.Selector(
        default="Set HRV Parameters",
        objects=["Set HRV Parameters", "Now the Files will be processed"],
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_PROCESS_HRV_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.default_btn.link(self, callbacks={"clicks": self.click_default_hrv})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_expert_hrv})
        self._view = pn.Column(
            self.header, pn.Row(self.skip_btn, self.default_btn, self.expert_mode_btn)
        )

    def click_skip(self, target, event):
        self.next_page = "Now the Files will be processed"
        self.skip_hrv = True
        self.ready = True

    def click_expert_hrv(self, target, event):
        self.next_page = "Set HRV Parameters"
        self.skip_hrv = False
        self.ready = True

    def click_default_hrv(self, target, event):
        self.next_page = "Now the Files will be processed"
        self.skip_hrv = False
        self.ready = True

    def panel(self):
        return self._view


class SetHRVParameters(PhysiologicalBase):
    select_hrv_types = pn.widgets.MultiChoice(
        name="Methods", value=["hrv_time", "hrv_nonlinear"], options=HRV_METHODS
    )
    check_correct_rpeaks = pn.widgets.Checkbox(name="Correct RPeaks", value=True)
    set_hrv_index_name = pn.widgets.TextInput(name="Index Name", value="")
    ready = param.Boolean(default=False)

    def __init__(self):
        super().__init__()
        self.update_text(PROCESS_HRV_TEXT)
        self.update_step(7)
        self.select_hrv_types.link(
            self, callbacks={"value": self.hrv_types_selection_changed}
        )
        self.check_correct_rpeaks.link(
            self, callbacks={"value": self.correct_rpeaks_checked}
        )
        self.set_hrv_index_name.link(
            self, callbacks={"value": self.hrv_index_name_changed}
        )
        self._view = pn.Column(
            self.header,
            self.select_hrv_types,
            self.check_correct_rpeaks,
            self.set_hrv_index_name,
        )

    def hrv_index_name_changed(self, _, event):
        self.hrv_index_name = event.new

    def correct_rpeaks_checked(self, _, event):
        self.correct_rpeaks = event.new

    def hrv_types_selection_changed(self, _, event):
        self.hrv_types = event.new

    def panel(self):
        return self._view


class PhysSignalType(PhysiologicalBase):
    ready = param.Boolean(default=False)
    select_signal = pn.widgets.Select(
        name="Select Signal Type",
        options=PHYSIOLOGICAL_SIGNAL_OPTIONS,
        sizing_mode="stretch_width",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SIGNAL_TYPE_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(SIGNAL_TYPE_TEXT)
        self.select_signal.link(self, callbacks={"value": self.signal_selected})
        self._view = pn.Column(self.header, self.select_signal)

    def signal_selected(self, _, event):
        self.signal = event.new if event.new in PHYSIOLOGICAL_SIGNAL_OPTIONS else ""
        if self.signal != "":
            self.ready = True
        else:
            self.ready = False

    def panel(self):
        self.ready = False
        return self._view

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class PhysiologicalPipeline:
    pipeline = None
    name = "Physiological"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True, inherit_params=True)

        self.pipeline.add_stage(
            "Select Physiological Session Type",
            PhysSignalType(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage("Sessions", Session())
        self.pipeline.add_stage(
            "Recordings",
            Recordings(),
            **{
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage("Multiple Files", Compress())
        self.pipeline.add_stage(
            "Upload Files",
            FileUpload(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Data arrived",
            DataArrived(),
            **{"ready_parameter": "proceed", "next_parameter": "next_page"},
        )
        self.pipeline.add_stage("Set RSP Parameters", SetRspParameters())
        self.pipeline.add_stage(
            "Select CFT Sheet",
            SelectCFTSheet(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Do you want to add time logs?",
            AskToAddTimes(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage(
            "Add Times",
            AddTimes(),
            **{"next_parameter": "next"},
        )
        self.pipeline.add_stage(
            "Frequency Bands",
            FrequencyBands(),
            **{"next_parameter": "next"},
        )
        self.pipeline.add_stage(
            "Do you want to detect Outlier?",
            AskToDetectOutliers(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage("Expert Outlier Detection", OutlierDetection())
        self.pipeline.add_stage(
            "Do you want to process the HRV also?",
            AskToProcessHRV(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Now the Files will be processed",
            ProcessingPreStep(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
            },
        )

        self.pipeline.add_stage("Set HRV Parameters", SetHRVParameters())
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage("Results", DownloadResults())
        self.pipeline.define_graph(
            {
                "Select Physiological Session Type": "Sessions",
                "Sessions": "Recordings",
                "Recordings": ("Multiple Files", "Upload Files"),
                "Multiple Files": "Upload Files",
                "Upload Files": "Data arrived",
                "Data arrived": (
                    "Do you want to add time logs?",
                    "Select CFT Sheet",
                    "Set RSP Parameters",
                ),
                "Set RSP Parameters": "Now the Files will be processed",
                "Select CFT Sheet": "Now the Files will be processed",
                "Do you want to add time logs?": (
                    "Add Times",
                    "Do you want to detect Outlier?",
                    "Frequency Bands",
                ),
                "Frequency Bands": "Now the Files will be processed",
                "Add Times": ("Do you want to detect Outlier?", "Frequency Bands"),
                "Do you want to detect Outlier?": (
                    "Expert Outlier Detection",
                    "Do you want to process the HRV also?",
                ),
                "Expert Outlier Detection": "Do you want to process the HRV also?",
                "Do you want to process the HRV also?": (
                    "Set HRV Parameters",
                    "Now the Files will be processed",
                ),
                "Set HRV Parameters": "Now the Files will be processed",
                "Now the Files will be processed": "Preview",
                "Preview": "Results",
            }
        )

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")


class MainPage(param.Parameterized):
    welcomeText = ""
    signalSelection = pn.GridBox(ncols=3)
    physBtn = pn.widgets.Button(name="Physiological Data", button_type="light")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    psychBtn = pn.widgets.Button(name="Psychological Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    mainPage = None

    def start_physiological_pipeline(self, event):
        ecg = PhysiologicalPipeline()
        return self.mainPage.append(pn.Column(ecg.pipeline))

    def __init__(self, main_page, **params):
        self.mainPage = main_page
        self.welcomeText = WELCOME_TEXT
        self.physBtn.on_click(self.start_physiological_pipeline)
        self.signalSelection.append(self.physBtn)
        super().__init__(**params)

    def view(self):
        return pn.Column(pn.pane.Markdown(self.welcomeText), self.signalSelection)



QUESTIONNAIRE_MAX_STEPS = 9

ASK_TO_SET_LOADING_PARAMETERS_TEXT = (
    "# Loading Parameters \\n\\n "
    "If you want to explicitly set loading parameters such as:"
    ' the Subject column, Condition column, etc. you can do so by clicking on the "'
    'Set Loading Parameters" button. '
    "This will take you to an additional step where you can set the loading parameters. "
    'Otherwise, click on "Default".'
)

LOAD_QUESTIONNAIRE_DATA_TEXT = (
    "# Set Loading Parameters \\n\\n"
    "Here you can set the loading parameters for your Questionnaire Data. "
)

LOADING_DATA_TEXT = (
    "# Upload Questionnaire Data \\n\\n"
    "Here you can upload your Questionnaire Data. "
    "In the following steps you can select the different Scores you want to calculate, "
    "and also convert them as well as plot your data."
)

SUGGEST_QUESTIONNAIRE_SCORES_TEXT = (
    "# Select Scores to Calculate\\n\\n"
    "In this step you may select the scores you want to calculate. "
    "You may add the Questionnaire you want to be analyzed "
    "(e.g. Perceived Stress Scale) as well as the pattern "
    "of the corresponding columns, where you can select "
    "the start and end of the columns."
)

CHECK_SELECTED_QUESTIONNAIRES_TEXT = (
    "# Check selected questionnaires\\n\\n"
    "In this step you may check the selected questionnaires "
    "and the corresponding columns. If you want to check them "
    'press the "Check Questionnaires" button. '
    "Otherwise, you may continue with the next step "
    "in which the scores will be computed."
)

ASK_TO_CONVERT_SCALES_TEXT = (
    "# Do you want to convert the scales of the selected questionnaires?\\n\\n"
    "If you want to change the scales of the selected questionnaires, "
    'click on the "Yes" button. Otherwise, click on the "No" button to proceed.'
)

CONVERT_SCALES_TEXT = "# Convert Scales"

ASK_TO_CROP_SCALE_TEXT = "# Would you like to crop the scale(s) of your data?"

CROP_SCALES_TEXT = (
    "# Crop scales\\n\\n"
    "Crop questionnaire scales, i.e., set values out of range to specific minimum and maximum values or to NaN."
)

ASK_TO_INVERT_SCORES_TEXT = "# Do you want to invert the scores of selected column(s) ?"

INVERT_SCORES_TEXT = "# Invert Scores"

SHOW_RESULTS_TEXT = "# Show Results"

ASK_TO_CHANGE_FORMAT_TEXT = (
    "# Do you want to change the format of your Dataframes? \\n "
    'If wou want to divide the Data of your questionnaires into different subscales please click on "Yes" '
    "otherwise you may skip that step."
)

CHANGE_FORMAT_TEXT = (
    "# Convert from wide to long format \\n "
    "In this step you can change the format of the dataframe(s) of your questionnaire(s).\\n"
    "Below you can select from the questionnaire(s) of the provided data in order to change the format."
    ' However only those questionnaire(s) which include column(s) that contain the symbol "_" are shown.'
)

DOWNLOAD_RESULTS_TEXT = "# Results"




class QuestionnaireBase(param.Parameterized):
    additional_index_cols = param.Dynamic(default=None)
    condition_col = param.String(default=None)
    data = param.Dynamic(default=None)
    data_in_long_format = param.Dynamic(default=None)
    data_scaled = param.Dynamic(default=None)
    data_scores = param.Dynamic()
    dict_scores = param.Dynamic(default={})
    progress = pn.indicators.Progress(
        name="Progress", height=20, sizing_mode="stretch_width"
    )
    results = param.Dynamic()
    replace_missing_vals = param.Boolean(default=False)
    remove_nan_rows = param.Boolean(default=False)
    sheet_name = param.Dynamic(default=0)
    step = param.Integer(default=1)
    subject_col = param.String(default=None)
    max_steps = QUESTIONNAIRE_MAX_STEPS

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, QUESTIONNAIRE_MAX_STEPS, header_text)
        super().__init__(**params)

    @staticmethod
    def get_progress(step) -> pn.indicators.Progress:
        return pn.indicators.Progress(
            name="Progress", height=20, sizing_mode="stretch_width", max=12, value=step
        )

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)

    @param.output(
        ("subject_col", param.String),
        ("condition_col", param.String),
        ("additional_index_cols", param.Dynamic),
        ("replace_missing_vals", param.Boolean),
        ("remove_nan_rows", param.Boolean),
        ("sheet_name", param.Dynamic),
        ("data", param.Dynamic),
        ("dict_scores", param.Dynamic),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
        ("results", param.Dynamic),
        ("data_in_long_format", param.Dynamic),
    )
    def output(self):
        return (
            self.subject_col,
            self.condition_col,
            self.additional_index_cols,
            self.replace_missing_vals,
            self.remove_nan_rows,
            self.sheet_name,
            self.data,
            self.dict_scores,
            self.data_scores,
            self.data_scaled,
            self.results,
            self.data_in_long_format,
        )


class AskToCropScale(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    crop_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Crop Scales",
        objects=["Crop Scales", "Ask to invert scores"],
    )

    def skip_crop(self, target, event):
        self.next_page = "Ask to invert scores"
        self.ready = True

    def crop_scales(self, target, event):
        self.next_page = "Crop Scales"
        self.ready = True

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_crop})
        self.crop_btn.link(self, callbacks={"clicks": self.crop_scales})
        self._view = pn.Column(
            self.header,
            pn.Row(self.crop_btn, self.skip_btn),
        )

    def panel(self):
        return self._view


class CropScales(QuestionnaireBase):
    crop_btn = pn.widgets.Button(name="Crop Scale", button_type="primary")
    questionnaire_selector = pn.widgets.Select(name="Questionnaire")
    set_nan_checkbox = pn.widgets.Checkbox(
        name="Set NaN values", visible=False, value=False
    )
    questionnaire_stat_values_df = pn.widgets.DataFrame(
        name="Statistical Values",
        visible=False,
        autosize_mode="force_fit",
        height=300,
    )
    score_range_arrayInput = pn.widgets.ArrayInput(name="Score Range")

    def selection_changed(self, target, event):
        if event.new == "":
            target[0].visible = False
            target[1].visible = False
            target[2].visible = False
            target[2].value = None
            self.crop_btn.visible = False
            self.set_nan_checkbox.value = False
            return
        questionnaire_data = self.data
        if self.data_scaled is not None:
            questionnaire_data = self.data_scaled
        questionnaire_data = questionnaire_data[self.dict_scores[event.new].to_list()]
        target[0].visible = bool(questionnaire_data.isnull().values.any())
        target[2].visible = True
        target[2].value = np.array(
            [questionnaire_data.to_numpy().min(), questionnaire_data.to_numpy().max()]
        )
        target[1].value = questionnaire_data.describe().transpose()[["min", "max"]]
        target[1].visible = True
        self.crop_btn.visible = True

    def crop_data(self, target, event):
        if self.questionnaire_selector.value is None:
            return
        key = self.questionnaire_selector.value
        if key is None or key not in self.dict_scores.keys():
            return
        set_nan = self.set_nan_checkbox.value
        cols = self.dict_scores[key].to_list()
        score_range = self.score_range_arrayInput.value
        if len(score_range) != 2:
            pn.state.notifications.error(
                "Score Range has the false length. It must be 2"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data
        try:
            self.data_scaled[cols] = bp.questionnaires.utils.crop_scale(
                data=self.data_scaled[cols],
                score_range=score_range,
                set_nan=set_nan,
                inplace=False,
            )
            self.questionnaire_stat_values_df.value = (
                self.data_scaled[cols].describe().transpose()
            )
            pn.state.notifications.success(
                f"Successfully cropped the data of questionnaire {key}"
            )
        except Exception as e:
            pn.state.notifications.error(f"Error while cropping the data: {e}")

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.crop_btn.link(self, callbacks={"clicks": self.crop_data})
        self.questionnaire_selector.link(
            (
                self.set_nan_checkbox,
                self.questionnaire_stat_values_df,
                self.score_range_arrayInput,
            ),
            callbacks={"value": self.selection_changed},
        )
        self._view = pn.Column(
            self.header,
            self.questionnaire_selector,
            self.score_range_arrayInput,
            self.set_nan_checkbox,
            self.questionnaire_stat_values_df,
            self.crop_btn,
        )

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        self.crop_btn.visible = False
        return self._view





class AskToChangeFormat(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    convert_to_long_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Change format"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(ASK_TO_CHANGE_FORMAT_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_converting_to_long})
        self.convert_to_long_btn.link(
            self, callbacks={"clicks": self.proceed_to_convert_to_long}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.convert_to_long_btn, self.skip_btn),
        )

    def skip_converting_to_long(self, target, event):
        self.next_page = "Download Results"
        self.ready = True

    def proceed_to_convert_to_long(self, target, event):
        self.next_page = "Change format"
        self.ready = True

    def panel(self):
        return self._view


class ConvertToLong(QuestionnaireBase):
    converting_panel_column = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(CHANGE_FORMAT_TEXT)
        self._view = pn.Column(
            self.header,
            self.converting_panel_column,
        )

    def converting_panel(self) -> pn.pane:
        acc = pn.Accordion()
        for questionnaire in self.dict_scores.keys():
            if not all(
                "_" in x for x in list(self.results.filter(like=questionnaire).columns)
            ):
                continue
            col = pn.Column()
            array_input = pn.widgets.ArrayInput(
                name=f"Index levels for {questionnaire}",
                placeholder='Enter your index levels. E.g. ["subscale","time"]',
            )

            change_btn = pn.widgets.Button(
                name=f"Change format of {questionnaire}",
                button_type="primary",
                disabled=True,
            )
            array_input.link(change_btn, callbacks={"value": self.validate_level_input})
            change_btn.link(
                (questionnaire, array_input), callbacks={"clicks": self.convert_to_long}
            )
            col.append(array_input)
            col.append(change_btn)
            acc.append((questionnaire, col))
        return acc

    @staticmethod
    def validate_level_input(target, event):
        if event.new is not None and len(event.new) != 0:
            target.disabled = False
        else:
            target.enabled = True

    def convert_to_long(self, target, event):
        questionnaire = target[0]
        levels = target[1].value
        if levels is None or len(levels) == 0:
            pn.state.notifications.error(
                "Please type in your desired levels and confirm them with enter"
            )
            return
        try:
            self.data_in_long_format = bp.utils.dataframe_handling.wide_to_long(
                self.results, stubname=questionnaire.upper(), levels=levels
            )
            pn.state.notifications.success(
                f"The format of {questionnaire} is now in long format"
            )
        except Exception as e:
            pn.state.notifications.error(f"The error {e} occurred")

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        if len(self.converting_panel_column.objects) == 0:
            self.converting_panel_column.append(self.converting_panel())
        else:
            self.converting_panel_column.__setitem__(0, self.converting_panel())
        return self._view





class SuggestQuestionnaireScores(QuestionnaireBase):
    accordion = pn.Accordion(sizing_mode="stretch_width")
    select_questionnaire = pn.widgets.Select(
        name="Choose Questionnaire:",
        options=list(bp.questionnaires.utils.get_supported_questionnaires().keys()),
    )
    add_questionnaire_btn = pn.widgets.Button(
        name="Add Questionnaire", button_type="primary", align="end"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SUGGEST_QUESTIONNAIRE_SCORES_TEXT
        super().__init__(**params)
        self.add_questionnaire_btn.link(
            self.select_questionnaire.value,
            callbacks={"clicks": self.add_questionnaire},
        )
        self.update_step(3)
        self.update_text(SUGGEST_QUESTIONNAIRE_SCORES_TEXT)

    def init_dict_scores(self):
        if bool(self.dict_scores):
            return
        for name in bp.questionnaires.utils.get_supported_questionnaires().keys():
            questionnaire_cols = self.data.filter(regex=f"(?i)({name})").columns
            list_col = list(questionnaire_cols)
            cols = {"-pre": [], "-post": [], "": []}
            for c in list_col:
                if "pre" in c.lower():
                    cols["-pre"].append(c)
                elif "post" in c.lower():
                    cols["-post"].append(c)
                else:
                    cols[""].append(c)
            for key in cols.keys():
                if len(cols[key]) != 0:
                    self.dict_scores[name + key] = pd.Index(data=cols[key])

    @staticmethod
    def edit_mode_on(target, event):
        target.disabled = (event.new % 2) == 0

    def change_columns(self, target, event):
        df = self.data[event.new]
        cols = df.columns
        self.dict_scores[target] = cols

    def get_accordion_item(self, questionnaire_key) -> pn.Column:
        col = pn.Column(name=questionnaire_key)
        height = min(400, 100 + len(self.data.columns.tolist()) * 5)
        edit_btn = pn.widgets.Button(name="Edit", button_type="primary")
        remove_btn = pn.widgets.Button(
            name="Remove",
            align="end",
            disabled=True,
            button_type="danger",
        )
        remove_btn.link(
            questionnaire_key,
            callbacks={"value": self.remove_questionnaire},
        )
        rename_field = pn.widgets.TextInput(name="Rename", disabled=True)
        rename_field.link(
            questionnaire_key,
            callbacks={"value": self.rename_questionnaire},
        )
        edit_btn.link(remove_btn, callbacks={"clicks": self.edit_mode_on})
        edit_btn.link(rename_field, callbacks={"clicks": self.edit_mode_on})
        col.append(edit_btn)
        col.append(remove_btn)
        col.append(rename_field)
        col.append(pn.layout.Divider())
        cross_selector = pn.widgets.CrossSelector(
            name=questionnaire_key,
            value=self.dict_scores[questionnaire_key].tolist(),
            options=self.data.columns.tolist(),
            height=height,
        )
        cross_selector.link(questionnaire_key, callbacks={"value": self.change_columns})
        col.append(cross_selector)
        return col

    def show_dict_scores(self):
        col = pn.Column()
        row = pn.Row()
        row.append(self.select_questionnaire)
        row.append(self.add_questionnaire_btn)
        gridBox = pn.GridBox(ncols=1)
        for questionnaire in self.dict_scores.keys():
            acc = self.get_accordion_item(questionnaire)
            self.accordion.append(acc)
        gridBox.append(self.accordion)
        col.append(gridBox)
        col.append(pn.layout.Divider())
        col.append(row)
        return col

    def remove_questionnaire(self, questionnaire_to_remove: str, _):
        try:
            index = [x.name for x in self.accordion.objects].index(
                questionnaire_to_remove
            )
            self.accordion.pop(index)
            self.dict_scores.pop(questionnaire_to_remove)
            pn.state.notifications.warning(
                f"Questionnaire {questionnaire_to_remove} was removed"
            )
        except ValueError as e:
            pn.state.notifications.error(
                f"Questionnaire {questionnaire_to_remove} could not be removed: {e}"
            )

    def add_questionnaire(self, selected_questionnaire, _):
        questionnaire = selected_questionnaire
        if questionnaire is None or questionnaire == "":
            pn.state.notifications.error("No Questionnaire selected")
            return
        i = 0
        while questionnaire in self.dict_scores.keys():
            questionnaire = self.select_questionnaire.value + f"-New{i}"
            i += 1
        self.dict_scores[questionnaire] = bp.questionnaires.utils.find_cols(
            data=self.data, contains=questionnaire
        )[1]
        self.accordion.append(self.get_accordion_item(questionnaire))

    def rename_questionnaire(self, target, event):
        old_name, new_name = target, event.new
        score = new_name
        if "-" in score:
            score_split = score.split("-")
            score = score_split[0]
        if score not in list(
            bp.questionnaires.utils.get_supported_questionnaires().keys()
        ):
            pn.state.notifications.error(f"Questionnaire: {score} not supported")
            return
        index = [x.name for x in self.accordion.objects].index(old_name)
        self.dict_scores[new_name] = self.dict_scores.pop(old_name)
        a = self.get_accordion_item(new_name)
        self.accordion.__setitem__(index, a)
        pn.state.notifications.success(
            f"Questionnaire {old_name} was renamed to {new_name}"
        )

    def panel(self):
        self.init_dict_scores()
        return pn.Column(self.header, self.show_dict_scores())


from biopsykit.utils.exceptions import ValidationError



class AskToConvertScales(QuestionnaireBase):
    next_page = param.Selector(
        default="Convert Scales",
        objects=["Convert Scales", "Ask To crop scales"],
    )
    convert_scales_btn = pn.widgets.Button(name="Yes")
    skip_converting_btn = pn.widgets.Button(name="No", button_type="primary")
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(ASK_TO_CONVERT_SCALES_TEXT)
        self.convert_scales_btn.link(self, callbacks={"clicks": self.convert_scales})
        self.skip_converting_btn.link(self, callbacks={"clicks": self.skip_converting})
        self._view = pn.Column(
            self.header,
            pn.Row(
                self.convert_scales_btn,
                self.skip_converting_btn,
            ),
        )

    def convert_scales(self, _, event):
        self.next_page = "Convert Scales"
        self.ready = True

    def skip_converting(self, _, event):
        self.next_page = "Ask To crop scales"
        self.ready = True

    def panel(self):
        return self._view


class ConvertScales(QuestionnaireBase):
    convert_column = pn.Column(sizing_mode="stretch_width")
    change_questionnaires_btn = pn.widgets.Button(name="Change Questionnaire scales")
    change_columns_btn = pn.widgets.Button(name="Change Columns", button_type="primary")
    change_columns_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )
    questionnaire_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(CONVERT_SCALES_TEXT)
        self.change_questionnaires_btn.link(
            self.questionnaire_col, callbacks={"clicks": self.show_questionnaire_col}
        )
        self.change_columns_btn.link(
            self.change_columns_col, callbacks={"clicks": self.show_name_col}
        )

    @staticmethod
    def activate_btn(target, event):
        if event.new is not None:
            target.disabled = False
        else:
            target.disabled = True

    @staticmethod
    def activate_col_btn(target, event):
        if type(event.new) is list:
            if len(event.new) == 0 or target[0].value is None:
                target[1].disabled = True
                return
        else:
            if event.new is None or len(target[0].value) == 0:
                target[1].disabled = True
                return
        target[1].disabled = False

    def apply_questionnaire_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        if self.data is None or self.data.empty or self.dict_scores is None:
            return
        key = target[0].value
        offset = target[1].value
        if key is None or not isinstance(key, str):
            pn.state.notifications.warning("No Questionnaire selected")
            return
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if key not in self.dict_scores.keys():
            pn.state.notifications.warning("No Questionnaire selected")
            return
        try:
            cols = self.dict_scores[key].to_list()
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of the questionnaire: {key} by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")

    def apply_column_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        cols = target[0].value
        if cols is None or len(cols) == 0:
            pn.state.notifications.warning("No Columns selected")
            return
        offset = target[1].value
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if any([col not in self.data.columns.to_list() for col in cols]):
            pn.state.notifications.warning("Not all columns are in the data")
            return
        try:
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of {len(cols)} Columns by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")
        except KeyError as ke:
            pn.state.notifications.error(f"Key Error: {ke}")

    def show_questionnaire_col(self, _, event):
        self.questionnaire_col.visible = True
        self.change_columns_col.visible = False
        if len(self.questionnaire_col.objects) == 0:
            self.questionnaire_col.append(self.get_questionnaire_col())
        elif len(self.questionnaire_col.objects) > 1:
            while len(self.questionnaire_col.objects) > 1:
                self.questionnaire_col.pop(0)
        elif (
            len(self.questionnaire_col.objects) == 1
            and self.questionnaire_col.objects[0].name is None
        ):
            self.questionnaire_col.__setitem__(0, self.get_questionnaire_col())

    def show_name_col(self, target, _):
        self.questionnaire_col.visible = False
        self.change_columns_col.visible = True
        if len(self.change_columns_col.objects) == 0:
            self.change_columns_col.append(self.get_column_col())
        elif len(self.change_columns_col.objects) > 1:
            while len(self.change_columns_col.objects) > 1:
                self.change_columns_col.pop(0)
        elif (
            len(self.change_columns_col.objects) == 1
            and self.change_columns_col.objects[0].name is None
        ):
            self.change_columns_col.__setitem__(0, self.get_column_col())

    def get_questionnaire_col(self) -> pn.Column:
        quest_col = pn.Column()
        select = pn.widgets.Select(
            name="Select Questionnaire", options=list(self.dict_scores.keys())
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder="Enter an offset for the selected columns",
            value=None,
        )
        row = pn.Row()
        row.append(select)
        row.append(input_offset)
        quest_col.append(row)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link(btn, callbacks={"value": self.activate_btn})
        btn.link(
            (select, input_offset),
            callbacks={"clicks": self.apply_questionnaire_scale},
        )
        quest_col.append(btn)
        return quest_col

    def get_column_col(self) -> pn.Column:
        col = pn.Column()
        crSel = pn.widgets.CrossSelector(
            name="Columns to invert the data",
            options=self.data.columns.to_list(),
            height=min(400, 100 + len(self.data.columns.tolist()) * 5),
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder=f"Enter an offset for the selected columns",
            value=None,
        )
        col.append(crSel)
        col.append(input_offset)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link((crSel, btn), callbacks={"value": self.activate_col_btn})
        crSel.link((input_offset, btn), callbacks={"value": self.activate_col_btn})
        btn.link((crSel, input_offset), callbacks={"clicks": self.apply_column_scale})
        col.append(btn)
        return col

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        return pn.Column(
            self.header,
            pn.Row(
                self.change_questionnaires_btn,
                self.change_columns_btn,
            ),
            self.convert_column,
            self.questionnaire_col,
            self.change_columns_col,
        )






class CheckSelectedQuestionnaires(QuestionnaireBase):
    check_btn = pn.widgets.Button(
        name="Check Questionnaires", sizing_mode="stretch_width"
    )
    questionnaire_panel = pn.Column(
        sizing_mode="stretch_width", objects=[pn.Accordion()]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHECK_SELECTED_QUESTIONNAIRES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(CHECK_SELECTED_QUESTIONNAIRES_TEXT)
        self.check_btn.link(self, callbacks={"clicks": self.check_questionnaires})
        self._view = pn.Column(
            self.header,
            self.check_btn,
            self.questionnaire_panel,
        )

    def init_questionnaire_panel(self, visible: bool) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width", visible=visible)
        for questionnaire in self.dict_scores.keys():
            df = self.data[list(self.dict_scores[questionnaire])]
            if df is None:
                continue
            df_widget = pn.widgets.Tabulator(
                df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=20,
                header_align="right",
                selectable=False,
            )
            filename, button = df_widget.download_menu(
                text_kwargs={"name": "Enter filename", "value": f"{questionnaire}.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            acc.append(
                (
                    questionnaire,
                    pn.Column(df_widget, pn.layout.Divider(), pn.Row(filename, button)),
                )
            )
        return acc

    def check_questionnaires(self, _, event):
        acc = self.init_questionnaire_panel((event.new % 2) != 0)
        self.questionnaire_panel.__setitem__(0, acc)

    def panel(self):
        if len(self.questionnaire_panel.objects) == 0:
            self.questionnaire_panel.append(self.init_questionnaire_panel(False))
        else:
            self.questionnaire_panel.__setitem__(
                0, self.init_questionnaire_panel(False)
            )
        return self._view
from biopsykit.utils.exceptions import ValidationError



class AskToConvertScales(QuestionnaireBase):
    next_page = param.Selector(
        default="Convert Scales",
        objects=["Convert Scales", "Ask To crop scales"],
    )
    convert_scales_btn = pn.widgets.Button(name="Yes")
    skip_converting_btn = pn.widgets.Button(name="No", button_type="primary")
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(ASK_TO_CONVERT_SCALES_TEXT)
        self.convert_scales_btn.link(self, callbacks={"clicks": self.convert_scales})
        self.skip_converting_btn.link(self, callbacks={"clicks": self.skip_converting})
        self._view = pn.Column(
            self.header,
            pn.Row(
                self.convert_scales_btn,
                self.skip_converting_btn,
            ),
        )

    def convert_scales(self, _, event):
        self.next_page = "Convert Scales"
        self.ready = True

    def skip_converting(self, _, event):
        self.next_page = "Ask To crop scales"
        self.ready = True

    def panel(self):
        return self._view


class ConvertScales(QuestionnaireBase):
    convert_column = pn.Column(sizing_mode="stretch_width")
    change_questionnaires_btn = pn.widgets.Button(name="Change Questionnaire scales")
    change_columns_btn = pn.widgets.Button(name="Change Columns", button_type="primary")
    change_columns_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )
    questionnaire_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(CONVERT_SCALES_TEXT)
        self.change_questionnaires_btn.link(
            self.questionnaire_col, callbacks={"clicks": self.show_questionnaire_col}
        )
        self.change_columns_btn.link(
            self.change_columns_col, callbacks={"clicks": self.show_name_col}
        )

    @staticmethod
    def activate_btn(target, event):
        if event.new is not None:
            target.disabled = False
        else:
            target.disabled = True

    @staticmethod
    def activate_col_btn(target, event):
        if type(event.new) is list:
            if len(event.new) == 0 or target[0].value is None:
                target[1].disabled = True
                return
        else:
            if event.new is None or len(target[0].value) == 0:
                target[1].disabled = True
                return
        target[1].disabled = False

    def apply_questionnaire_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        if self.data is None or self.data.empty or self.dict_scores is None:
            return
        key = target[0].value
        offset = target[1].value
        if key is None or not isinstance(key, str):
            pn.state.notifications.warning("No Questionnaire selected")
            return
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if key not in self.dict_scores.keys():
            pn.state.notifications.warning("No Questionnaire selected")
            return
        try:
            cols = self.dict_scores[key].to_list()
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of the questionnaire: {key} by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")

    def apply_column_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        cols = target[0].value
        if cols is None or len(cols) == 0:
            pn.state.notifications.warning("No Columns selected")
            return
        offset = target[1].value
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if any([col not in self.data.columns.to_list() for col in cols]):
            pn.state.notifications.warning("Not all columns are in the data")
            return
        try:
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of {len(cols)} Columns by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")
        except KeyError as ke:
            pn.state.notifications.error(f"Key Error: {ke}")

    def show_questionnaire_col(self, _, event):
        self.questionnaire_col.visible = True
        self.change_columns_col.visible = False
        if len(self.questionnaire_col.objects) == 0:
            self.questionnaire_col.append(self.get_questionnaire_col())
        elif len(self.questionnaire_col.objects) > 1:
            while len(self.questionnaire_col.objects) > 1:
                self.questionnaire_col.pop(0)
        elif (
            len(self.questionnaire_col.objects) == 1
            and self.questionnaire_col.objects[0].name is None
        ):
            self.questionnaire_col.__setitem__(0, self.get_questionnaire_col())

    def show_name_col(self, target, _):
        self.questionnaire_col.visible = False
        self.change_columns_col.visible = True
        if len(self.change_columns_col.objects) == 0:
            self.change_columns_col.append(self.get_column_col())
        elif len(self.change_columns_col.objects) > 1:
            while len(self.change_columns_col.objects) > 1:
                self.change_columns_col.pop(0)
        elif (
            len(self.change_columns_col.objects) == 1
            and self.change_columns_col.objects[0].name is None
        ):
            self.change_columns_col.__setitem__(0, self.get_column_col())

    def get_questionnaire_col(self) -> pn.Column:
        quest_col = pn.Column()
        select = pn.widgets.Select(
            name="Select Questionnaire", options=list(self.dict_scores.keys())
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder="Enter an offset for the selected columns",
            value=None,
        )
        row = pn.Row()
        row.append(select)
        row.append(input_offset)
        quest_col.append(row)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link(btn, callbacks={"value": self.activate_btn})
        btn.link(
            (select, input_offset),
            callbacks={"clicks": self.apply_questionnaire_scale},
        )
        quest_col.append(btn)
        return quest_col

    def get_column_col(self) -> pn.Column:
        col = pn.Column()
        crSel = pn.widgets.CrossSelector(
            name="Columns to invert the data",
            options=self.data.columns.to_list(),
            height=min(400, 100 + len(self.data.columns.tolist()) * 5),
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder=f"Enter an offset for the selected columns",
            value=None,
        )
        col.append(crSel)
        col.append(input_offset)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link((crSel, btn), callbacks={"value": self.activate_col_btn})
        crSel.link((input_offset, btn), callbacks={"value": self.activate_col_btn})
        btn.link((crSel, input_offset), callbacks={"clicks": self.apply_column_scale})
        col.append(btn)
        return col

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        return pn.Column(
            self.header,
            pn.Row(
                self.change_questionnaires_btn,
                self.change_columns_btn,
            ),
            self.convert_column,
            self.questionnaire_col,
            self.change_columns_col,
        )



class AskToCropScale(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    crop_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Crop Scales",
        objects=["Crop Scales", "Ask to invert scores"],
    )

    def skip_crop(self, target, event):
        self.next_page = "Ask to invert scores"
        self.ready = True

    def crop_scales(self, target, event):
        self.next_page = "Crop Scales"
        self.ready = True

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_crop})
        self.crop_btn.link(self, callbacks={"clicks": self.crop_scales})
        self._view = pn.Column(
            self.header,
            pn.Row(self.crop_btn, self.skip_btn),
        )

    def panel(self):
        return self._view


class CropScales(QuestionnaireBase):
    crop_btn = pn.widgets.Button(name="Crop Scale", button_type="primary")
    questionnaire_selector = pn.widgets.Select(name="Questionnaire")
    set_nan_checkbox = pn.widgets.Checkbox(
        name="Set NaN values", visible=False, value=False
    )
    questionnaire_stat_values_df = pn.widgets.DataFrame(
        name="Statistical Values",
        visible=False,
        autosize_mode="force_fit",
        height=300,
    )
    score_range_arrayInput = pn.widgets.ArrayInput(name="Score Range")

    def selection_changed(self, target, event):
        if event.new == "":
            target[0].visible = False
            target[1].visible = False
            target[2].visible = False
            target[2].value = None
            self.crop_btn.visible = False
            self.set_nan_checkbox.value = False
            return
        questionnaire_data = self.data
        if self.data_scaled is not None:
            questionnaire_data = self.data_scaled
        questionnaire_data = questionnaire_data[self.dict_scores[event.new].to_list()]
        target[0].visible = bool(questionnaire_data.isnull().values.any())
        target[2].visible = True
        target[2].value = np.array(
            [questionnaire_data.to_numpy().min(), questionnaire_data.to_numpy().max()]
        )
        target[1].value = questionnaire_data.describe().transpose()[["min", "max"]]
        target[1].visible = True
        self.crop_btn.visible = True

    def crop_data(self, target, event):
        if self.questionnaire_selector.value is None:
            return
        key = self.questionnaire_selector.value
        if key is None or key not in self.dict_scores.keys():
            return
        set_nan = self.set_nan_checkbox.value
        cols = self.dict_scores[key].to_list()
        score_range = self.score_range_arrayInput.value
        if len(score_range) != 2:
            pn.state.notifications.error(
                "Score Range has the false length. It must be 2"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data
        try:
            self.data_scaled[cols] = bp.questionnaires.utils.crop_scale(
                data=self.data_scaled[cols],
                score_range=score_range,
                set_nan=set_nan,
                inplace=False,
            )
            self.questionnaire_stat_values_df.value = (
                self.data_scaled[cols].describe().transpose()
            )
            pn.state.notifications.success(
                f"Successfully cropped the data of questionnaire {key}"
            )
        except Exception as e:
            pn.state.notifications.error(f"Error while cropping the data: {e}")

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.crop_btn.link(self, callbacks={"clicks": self.crop_data})
        self.questionnaire_selector.link(
            (
                self.set_nan_checkbox,
                self.questionnaire_stat_values_df,
                self.score_range_arrayInput,
            ),
            callbacks={"value": self.selection_changed},
        )
        self._view = pn.Column(
            self.header,
            self.questionnaire_selector,
            self.score_range_arrayInput,
            self.set_nan_checkbox,
            self.questionnaire_stat_values_df,
            self.crop_btn,
        )

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        self.crop_btn.visible = False
        return self._view




class DownloadQuestionnaireResults(QuestionnaireBase):
    load_results_btn = pn.widgets.Button(name="Download Results", button_type="primary")
    zip_buffer = io.BytesIO()
    download = pn.widgets.FileDownload(
        name="Load Questionnaire Results",
        filename="Results.zip",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = DOWNLOAD_RESULTS_TEXT
        super().__init__(**params)
        self.update_step(9)
        self.update_text(DOWNLOAD_RESULTS_TEXT)
        self.download.callback = pn.bind(self.load_results)
        self._view = pn.Column(
            self.header,
            self.download,
        )

    def load_results(self):
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            supported_questionnaires = (
                bp.questionnaires.utils.get_supported_questionnaires()
            )
            for questionnaire in supported_questionnaires:
                questionnaire_results = self.results.filter(like=questionnaire.upper())
                if questionnaire_results.empty:
                    continue
                questionnaire_results.to_excel(
                    f"{questionnaire}_results_.xlsx",
                    sheet_name=questionnaire,
                )
                zip_file.write(f"{questionnaire}_results_.xlsx")
        self.zip_buffer.seek(0)
        return self.zip_buffer

    def panel(self):
        self.download.callback = pn.bind(self.load_results)
        self.download.filename = "Results.zip"
        self.download.name = "Download Results"
        self.download.param.update()
        return self._view



class AskToInvertScores(QuestionnaireBase):
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Invert scores",
        objects=["Invert scores", "Show Results"],
    )
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    invert_scores_btn = pn.widgets.Button(name="Yes")

    def skip_inverting(self, target, event):
        self.next_page = "Show Results"
        self.ready = True

    def invert_scores(self, target, event):
        self.next_page = "Invert scores"
        self.ready = True

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_INVERT_SCORES_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(ASK_TO_INVERT_SCORES_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_inverting})
        self.invert_scores_btn.link(self, callbacks={"clicks": self.invert_scores})
        self._view = pn.Column(
            self.header,
            pn.Row(self.invert_scores_btn, self.skip_btn),
        )

    def panel(self):
        return self._view


class InvertScores(QuestionnaireBase):
    questionnaire_selector = pn.widgets.Select(name="Select Questionnaire")
    select_all_checkbox = pn.widgets.Checkbox(
        name="Select All", value=False, visible=False
    )
    column_cross_selector = pn.widgets.CrossSelector(
        name="Select Column(s)", visible=False
    )
    invert_scores_btn = pn.widgets.Button(name="Invert the scores", visible=False)
    score_range_array_input = pn.widgets.ArrayInput(
        name="Score Range", value=np.array([0, 0]), visible=False
    )

    def questionnaire_changed(self, _, event):
        questionnaire = event.new
        if questionnaire == "" or questionnaire is None:
            self.select_all_checkbox.visible = False
            self.column_cross_selector.visible = False
            self.invert_scores_btn.visible = False
            self.score_range_array_input.visible = False
            return
        self.select_all_checkbox.value = False
        self.select_all_checkbox.visible = True
        self.column_cross_selector.options = self.dict_scores[questionnaire].to_list()
        self.column_cross_selector.height = min(
            400, 100 + len(self.data.columns.tolist()) * 5
        )
        self.column_cross_selector.visible = True
        self.score_range_array_input.value = np.array([0, 0])
        self.score_range_array_input.visible = True
        self.invert_scores_btn.visible = True

    def select_all_checked(self, _, event):
        if (
            event.new
            and self.questionnaire_selector.value is not None
            and self.questionnaire_selector.value != ""
        ):
            self.column_cross_selector.value = self.dict_scores[
                self.questionnaire_selector.value
            ].to_list()
        else:
            self.column_cross_selector.value = []
            self.select_all_checkbox.value = False

    def invert_scores(self, target, event):
        if len(self.column_cross_selector.value) == 0:
            pn.state.notifications.error(
                "You have to select at least one column to invert the scores"
            )
            return
        if len(self.score_range_array_input.value) != 2:
            pn.state.notifications.error(
                "You have to fill out the field Score Range in a format like : [1,2]"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data.copy()
        try:
            self.data_scaled = bp.questionnaires.utils.invert(
                data=self.data_scaled,
                score_range=self.score_range_array_input.value,
                cols=self.column_cross_selector.value,
                inplace=False,
            )
            pn.state.notifications.success(
                f"Successfully inverted the scores of the selected columns to the range {self.score_range_array_input.value}"
            )
        except Exception as e:
            pn.state.notifications.error(
                f"Error occured while inverting the selected columns: {e}"
            )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_INVERT_SCORES_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(ASK_TO_INVERT_SCORES_TEXT)
        self.questionnaire_selector.link(
            self, callbacks={"value": self.questionnaire_changed}
        )
        self.select_all_checkbox.link(
            self, callbacks={"value": self.select_all_checked}
        )
        self.invert_scores_btn.link(self, callbacks={"clicks": self.invert_scores})
        self._view = pn.Column(
            self.header,
            self.questionnaire_selector,
            self.select_all_checkbox,
            self.column_cross_selector,
            self.invert_scores_btn,
        )

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        return self._view



class AskToSetLoadingParameters(QuestionnaireBase):
    next = param.Selector(
        default="Upload Questionnaire Data",
        objects=["Upload Questionnaire Data", "Set Loading Parameters"],
    )
    ready = param.Boolean(default=False)
    default_btn = pn.widgets.Button(name="Default")
    set_parameters_manually = pn.widgets.Button(
        name="Set Loading Parameters",
        button_type="primary",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_SET_LOADING_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(ASK_TO_SET_LOADING_PARAMETERS_TEXT)
        self.set_parameters_manually.on_click(self.click_set_parameters)
        self.default_btn.on_click(self.click_default)
        self._view = pn.Column(
            self.header,
            pn.Row(self.default_btn, self.set_parameters_manually),
        )

    def click_default(self, _):
        self.next = "Upload Questionnaire Data"
        self.ready = True

    def click_set_parameters(self, _):
        self.next = "Set Loading Parameters"
        self.ready = True

    def panel(self):
        return self._view


class SetLoadingParametersManually(QuestionnaireBase):
    select_subject_col = pn.widgets.TextInput(
        name="subject_col",
        value=None,
        placeholder="Enter the name of your subject column",
    )
    set_condition_col = pn.widgets.TextInput(
        name="condition_col",
        value=None,
        placeholder="Enter the name of your condition column",
    )
    set_additional_index_cols = pn.widgets.ArrayInput(
        name="additional_index_cols", value=None
    )
    check_replace_missing_vals = pn.widgets.Checkbox(
        name="replace_missing_vals", value=True
    )
    check_remove_nan_rows = pn.widgets.Checkbox(name="remove_nan_rows", value=True)
    set_sheet_name = pn.widgets.TextInput(
        name="sheet_name",
        value="0",
        placeholder="Enter the name or index of the sheet",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOAD_QUESTIONNAIRE_DATA_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(LOAD_QUESTIONNAIRE_DATA_TEXT)
        self.select_subject_col.link(
            self, callbacks={"value": self.selected_subject_col_changed}
        )
        self.set_condition_col.link(
            self, callbacks={"value": self.condition_col_changed}
        )
        self.set_additional_index_cols.link(
            self, callbacks={"value": self.additional_index_cols_changed}
        )
        self.check_replace_missing_vals.link(
            self, callbacks={"value": self.check_replace_missing_vals_changed}
        )
        self.check_remove_nan_rows.link(
            self, callbacks={"value": self.remove_nan_rows_changed}
        )
        self.set_sheet_name.link(self, callbacks={"value": self.sheet_name_changed})
        self._view = pn.Column(
            self.header,
            self.select_subject_col,
            self.set_condition_col,
            self.set_additional_index_cols,
            self.check_replace_missing_vals,
            self.check_remove_nan_rows,
            self.set_sheet_name,
        )

    def sheet_name_changed(self, _, event):
        sheet_name = event.new
        if sheet_name.isnumeric():
            self.sheet_name = int(sheet_name)
        else:
            self.sheet_name = event.new

    def remove_nan_rows_changed(self, _, event):
        self.remove_nan_rows = event.new

    def check_replace_missing_vals_changed(self, _, event):
        self.replace_missing_vals = event.new

    def additional_index_cols_changed(self, _, event):
        self.additional_index_cols = event.new

    def condition_col_changed(self, _, event):
        self.condition_col = event.new

    def selected_subject_col_changed(self, _, event):
        self.subject_col = event.new

    def panel(self):
        return self._view



class SuggestQuestionnaireScores(QuestionnaireBase):
    accordion = pn.Accordion(sizing_mode="stretch_width")
    select_questionnaire = pn.widgets.Select(
        name="Choose Questionnaire:",
        options=list(bp.questionnaires.utils.get_supported_questionnaires().keys()),
    )
    add_questionnaire_btn = pn.widgets.Button(
        name="Add Questionnaire", button_type="primary", align="end"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SUGGEST_QUESTIONNAIRE_SCORES_TEXT
        super().__init__(**params)
        self.add_questionnaire_btn.link(
            self.select_questionnaire.value,
            callbacks={"clicks": self.add_questionnaire},
        )
        self.update_step(3)
        self.update_text(SUGGEST_QUESTIONNAIRE_SCORES_TEXT)

    def init_dict_scores(self):
        if bool(self.dict_scores):
            return
        for name in bp.questionnaires.utils.get_supported_questionnaires().keys():
            questionnaire_cols = self.data.filter(regex=f"(?i)({name})").columns
            list_col = list(questionnaire_cols)
            cols = {"-pre": [], "-post": [], "": []}
            for c in list_col:
                if "pre" in c.lower():
                    cols["-pre"].append(c)
                elif "post" in c.lower():
                    cols["-post"].append(c)
                else:
                    cols[""].append(c)
            for key in cols.keys():
                if len(cols[key]) != 0:
                    self.dict_scores[name + key] = pd.Index(data=cols[key])

    @staticmethod
    def edit_mode_on(target, event):
        target.disabled = (event.new % 2) == 0

    def change_columns(self, target, event):
        df = self.data[event.new]
        cols = df.columns
        self.dict_scores[target] = cols

    def get_accordion_item(self, questionnaire_key) -> pn.Column:
        col = pn.Column(name=questionnaire_key)
        height = min(400, 100 + len(self.data.columns.tolist()) * 5)
        edit_btn = pn.widgets.Button(name="Edit", button_type="primary")
        remove_btn = pn.widgets.Button(
            name="Remove",
            align="end",
            disabled=True,
            button_type="danger",
        )
        remove_btn.link(
            questionnaire_key,
            callbacks={"value": self.remove_questionnaire},
        )
        rename_field = pn.widgets.TextInput(name="Rename", disabled=True)
        rename_field.link(
            questionnaire_key,
            callbacks={"value": self.rename_questionnaire},
        )
        edit_btn.link(remove_btn, callbacks={"clicks": self.edit_mode_on})
        edit_btn.link(rename_field, callbacks={"clicks": self.edit_mode_on})
        col.append(edit_btn)
        col.append(remove_btn)
        col.append(rename_field)
        col.append(pn.layout.Divider())
        cross_selector = pn.widgets.CrossSelector(
            name=questionnaire_key,
            value=self.dict_scores[questionnaire_key].tolist(),
            options=self.data.columns.tolist(),
            height=height,
        )
        cross_selector.link(questionnaire_key, callbacks={"value": self.change_columns})
        col.append(cross_selector)
        return col

    def show_dict_scores(self):
        col = pn.Column()
        row = pn.Row()
        row.append(self.select_questionnaire)
        row.append(self.add_questionnaire_btn)
        gridBox = pn.GridBox(ncols=1)
        for questionnaire in self.dict_scores.keys():
            acc = self.get_accordion_item(questionnaire)
            self.accordion.append(acc)
        gridBox.append(self.accordion)
        col.append(gridBox)
        col.append(pn.layout.Divider())
        col.append(row)
        return col

    def remove_questionnaire(self, questionnaire_to_remove: str, _):
        try:
            index = [x.name for x in self.accordion.objects].index(
                questionnaire_to_remove
            )
            self.accordion.pop(index)
            self.dict_scores.pop(questionnaire_to_remove)
            pn.state.notifications.warning(
                f"Questionnaire {questionnaire_to_remove} was removed"
            )
        except ValueError as e:
            pn.state.notifications.error(
                f"Questionnaire {questionnaire_to_remove} could not be removed: {e}"
            )

    def add_questionnaire(self, selected_questionnaire, _):
        questionnaire = selected_questionnaire
        if questionnaire is None or questionnaire == "":
            pn.state.notifications.error("No Questionnaire selected")
            return
        i = 0
        while questionnaire in self.dict_scores.keys():
            questionnaire = self.select_questionnaire.value + f"-New{i}"
            i += 1
        self.dict_scores[questionnaire] = bp.questionnaires.utils.find_cols(
            data=self.data, contains=questionnaire
        )[1]
        self.accordion.append(self.get_accordion_item(questionnaire))

    def rename_questionnaire(self, target, event):
        old_name, new_name = target, event.new
        score = new_name
        if "-" in score:
            score_split = score.split("-")
            score = score_split[0]
        if score not in list(
            bp.questionnaires.utils.get_supported_questionnaires().keys()
        ):
            pn.state.notifications.error(f"Questionnaire: {score} not supported")
            return
        index = [x.name for x in self.accordion.objects].index(old_name)
        self.dict_scores[new_name] = self.dict_scores.pop(old_name)
        a = self.get_accordion_item(new_name)
        self.accordion.__setitem__(index, a)
        pn.state.notifications.success(
            f"Questionnaire {old_name} was renamed to {new_name}"
        )

    def panel(self):
        self.init_dict_scores()
        return pn.Column(self.header, self.show_dict_scores())



class ShowResults(QuestionnaireBase):

    text = "# Show Results"
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Ask to change format"],
    )
    questionnaire_results_Column = pn.Column()

    def show_questionnaire_results(self) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width")
        supported_questionnaires = (
            bp.questionnaires.utils.get_supported_questionnaires()
        )
        for questionnaire in supported_questionnaires:
            questionnaire_results = self.results.filter(like=questionnaire.upper())
            if questionnaire_results.empty:
                continue
            tabulator = pn.widgets.Tabulator(
                questionnaire_results,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
            )
            filename, button = tabulator.download_menu(
                text_kwargs={
                    "name": "Enter filename",
                    "value": f"{questionnaire}_results.csv",
                },
                button_kwargs={
                    "name": "Download Results",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            acc.append(
                (
                    questionnaire,
                    pn.Column(tabulator, pn.layout.Divider(), pn.Row(filename, button)),
                )
            )
        return acc

    def __init__(self, **params):
        params["HEADER_TEXT"] = SHOW_RESULTS_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(SHOW_RESULTS_TEXT)
        self._view = pn.Column(self.header, self.questionnaire_results_Column)

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data.copy()
        self.results = bp.questionnaires.utils.compute_scores(
            data=self.data_scaled, quest_dict=self.dict_scores
        )
        if all("_" in cols for cols in self.results.columns.to_list()):
            self.next_page = "Ask to change format"
        if len(self.questionnaire_results_Column.objects) == 0:
            self.questionnaire_results_Column.append(self.show_questionnaire_results())
        else:
            self.questionnaire_results_Column.__setitem__(
                0, self.show_questionnaire_results()
            )
        return self._view



class UploadQuestionnaireData(QuestionnaireBase):
    ready = param.Boolean(default=False)
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xls,.xlsx",
    )

    def parse_file_input(self, _, event):
        try:
            pn.state.notifications.info("Loading data")
            self.data = load_questionnaire_data(
                file=self.file_input.value,
                file_name=self.file_input.filename,
                subject_col=self.subject_col,
                condition_col=self.condition_col,
                additional_index_cols=self.additional_index_cols,
                replace_missing_vals=self.replace_missing_vals,
                remove_nan_rows=self.remove_nan_rows,
                sheet_name=self.sheet_name,
            )
            self.data_scaled = self.data.copy()
            self.ready = True
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOADING_DATA_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(LOADING_DATA_TEXT)
        self.file_input.link(self, callbacks={"value": self.parse_file_input})
        self._view = pn.Column(
            self.header,
            self.file_input,
        )

    def panel(self):
        return self._view



class AskToChangeFormat(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    convert_to_long_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Change format"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(ASK_TO_CHANGE_FORMAT_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_converting_to_long})
        self.convert_to_long_btn.link(
            self, callbacks={"clicks": self.proceed_to_convert_to_long}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.convert_to_long_btn, self.skip_btn),
        )

    def skip_converting_to_long(self, target, event):
        self.next_page = "Download Results"
        self.ready = True

    def proceed_to_convert_to_long(self, target, event):
        self.next_page = "Change format"
        self.ready = True

    def panel(self):
        return self._view


class ConvertToLong(QuestionnaireBase):
    converting_panel_column = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(CHANGE_FORMAT_TEXT)
        self._view = pn.Column(
            self.header,
            self.converting_panel_column,
        )

    def converting_panel(self) -> pn.pane:
        acc = pn.Accordion()
        for questionnaire in self.dict_scores.keys():
            if not all(
                "_" in x for x in list(self.results.filter(like=questionnaire).columns)
            ):
                continue
            col = pn.Column()
            array_input = pn.widgets.ArrayInput(
                name=f"Index levels for {questionnaire}",
                placeholder='Enter your index levels. E.g. ["subscale","time"]',
            )

            change_btn = pn.widgets.Button(
                name=f"Change format of {questionnaire}",
                button_type="primary",
                disabled=True,
            )
            array_input.link(change_btn, callbacks={"value": self.validate_level_input})
            change_btn.link(
                (questionnaire, array_input), callbacks={"clicks": self.convert_to_long}
            )
            col.append(array_input)
            col.append(change_btn)
            acc.append((questionnaire, col))
        return acc

    @staticmethod
    def validate_level_input(target, event):
        if event.new is not None and len(event.new) != 0:
            target.disabled = False
        else:
            target.enabled = True

    def convert_to_long(self, target, event):
        questionnaire = target[0]
        levels = target[1].value
        if levels is None or len(levels) == 0:
            pn.state.notifications.error(
                "Please type in your desired levels and confirm them with enter"
            )
            return
        try:
            self.data_in_long_format = bp.utils.dataframe_handling.wide_to_long(
                self.results, stubname=questionnaire.upper(), levels=levels
            )
            pn.state.notifications.success(
                f"The format of {questionnaire} is now in long format"
            )
        except Exception as e:
            pn.state.notifications.error(f"The error {e} occurred")

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        if len(self.converting_panel_column.objects) == 0:
            self.converting_panel_column.append(self.converting_panel())
        else:
            self.converting_panel_column.__setitem__(0, self.converting_panel())
        return self._view

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class QuestionnairePipeline:
    pipeline = None
    name = "Questionnaire"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True, inherit_params=True)
        self.pipeline.add_stage(
            "Ask for additional parameters",
            AskToSetLoadingParameters(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage(
            "Set Loading Parameters", SetLoadingParametersManually()
        )
        self.pipeline.add_stage(
            "Upload Questionnaire Data",
            UploadQuestionnaireData(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
            },
        )
        self.pipeline.add_stage("Set Questionnaires", SuggestQuestionnaireScores())
        self.pipeline.add_stage(
            "Check selected Questionnaires", CheckSelectedQuestionnaires()
        )
        self.pipeline.add_stage(
            "Ask to convert scales",
            AskToConvertScales(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Convert Scales", ConvertScales())

        self.pipeline.add_stage(
            "Ask To crop scales",
            AskToCropScale(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Crop Scales", CropScales())

        self.pipeline.add_stage(
            "Ask to invert scores",
            AskToInvertScores(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Invert scores", InvertScores())
        self.pipeline.add_stage(
            "Show Results",
            ShowResults(),
            **{
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Ask to change format",
            AskToChangeFormat(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage("Change format", ConvertToLong())

        self.pipeline.add_stage("Download Results", DownloadQuestionnaireResults())

        self.pipeline.define_graph(
            {
                "Ask for additional parameters": (
                    "Set Loading Parameters",
                    "Upload Questionnaire Data",
                ),
                "Set Loading Parameters": "Upload Questionnaire Data",
                "Upload Questionnaire Data": "Set Questionnaires",
                "Set Questionnaires": "Check selected Questionnaires",
                "Check selected Questionnaires": "Ask to convert scales",
                "Ask to convert scales": ("Convert Scales", "Ask To crop scales"),
                "Convert Scales": "Ask To crop scales",
                "Ask To crop scales": ("Crop Scales", "Ask to invert scores"),
                "Crop Scales": "Ask to invert scores",
                "Ask to invert scores": (
                    "Invert scores",
                    "Show Results",
                ),
                "Invert scores": "Show Results",
                "Show Results": ("Download Results", "Ask to change format"),
                "Ask to change format": ("Download Results", "Change format"),
                "Change format": "Download Results",
            }
        )





class TrimSession(PhysiologicalBase):
    start_time = pn.widgets.DatetimePicker(name="Start time")
    stop_time = pn.widgets.DatetimePicker(name="Stop time")
    trim_btn = pn.widgets.Button(name="Trim", button_type="primary")
    min_time = None
    max_time = None

    def __init__(self):
        super().__init__()
        self.step = 10
        self.update_step(self.step)
        text = (
            "# Edit start and stop \\n \\n"
            "Here you can manually change the "
            "start and the stop times for your session."
        )
        self.update_text(text)
        self.trim_btn.link(self, callbacks={"clicks": self.trim_data})
        pane = pn.Column(
            self.header,
            self.start_time,
            self.stop_time,
            self.trim_btn,
        )
        self._view = pane

    def limit_times(self):
        min_time_all = None
        max_time_all = None
        if type(self.original_data) is pd.DataFrame:
            start_end = get_start_and_end_time(self.original_data)
            if start_end is None:
                return
            min_time_all = timezone_aware_to_naive(start_end[0])
            max_time_all = timezone_aware_to_naive(start_end[1])
        elif type(self.original_data) is dict:
            for df in self.original_data.values():
                min_max = get_start_and_end_time(df)
                df_min = timezone_aware_to_naive(min_max[0])
                df_max = timezone_aware_to_naive(min_max[1])
                if min_time_all is None or min_time_all > df_min:
                    min_time_all = df_min
                if max_time_all is None or max_time_all < df_max:
                    max_time_all = df_max
        if min_time_all is None or max_time_all is None:
            return
        self.min_time = min_time_all
        self.max_time = max_time_all
        self.start_time.start = self.min_time
        self.start_time.end = self.max_time
        self.stop_time.start = self.min_time
        self.stop_time.end = self.max_time
        self.start_time.value = self.min_time
        self.stop_time.value = self.max_time

    @pn.depends("start_time.value", watch=True)
    def start_time_changed(self):
        if self.stop_time.value is None or self.start_time.value is None:
            return
        if self.stop_time.value < self.start_time.value:
            self.stop_time.value = self.start_time.value
            pn.state.notifications.warning(
                "Stop time is lower than the selected start time!"
            )

    @pn.depends("stop_time.value", watch=True)
    def stop_time_changed(self):
        if self.stop_time.value is None or self.start_time.value is None:
            return
        if self.stop_time.value < self.start_time.value:
            self.start_time.value = self.stop_time.value
            pn.state.notifications.warning(
                "s time is lower than the selected start time!"
            )

    def trim_data(self, target, event):
        print(self.trim_btn.clicks)
        if type(self.original_data) is pd.DataFrame:
            dt_col = get_datetime_columns_of_data_frame(self.original_data)
            if len(dt_col) == 1:
                col = dt_col[0]
                start = self.start_time.value
                stop = self.stop_time.value
                tz = pytz.timezone(self.timezone)
                start = tz.localize(start)
                stop = tz.localize(stop)
                self.trimmed_data = self.original_data.loc[
                    (self.original_data[col] >= start)
                    & (self.original_data[col] <= stop)
                ]
        elif type(self.original_data) is dict:
            keys = list(self.original_data.keys())
            for key in keys:
                dt_col = get_datetime_columns_of_data_frame(self.original_data[key])
                if len(dt_col) == 1:
                    col = dt_col[0]
                    start = self.start_time.value
                    stop = self.stop_time.value
                    tz = pytz.timezone(self.timezone)
                    start = tz.localize(start)
                    stop = tz.localize(stop)
                    df = self.original_data[key]
                    if col == "index":
                        df = df.between_time(start.time(), stop.time())
                        self.trimmed_data[key] = df
                    else:
                        df = df.loc[(df[col] >= start) & (df[col] <= stop)]
                        self.trimmed_data[key] = df
        else:
            print("session")

    def panel(self):
        self.trimmed_data = self.original_data
        self.limit_times()
        return self._view



os.environ["OUTDATED_IGNORE"] = "1"


pn.extension(sizing_mode="stretch_width")
pn.extension(
    "plotly",
    sizing_mode="stretch_width",
)
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")


pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")


class MainPage(param.Parameterized):
    welcomeText = ""
    signalSelection = pn.GridBox(ncols=3)
    physBtn = pn.widgets.Button(name="Physiological Data", button_type="light")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    psychBtn = pn.widgets.Button(name="Psychological Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    mainPage = None

    def start_physiological_pipeline(self, event):
        ecg = PhysiologicalPipeline()
        return self.mainPage.append(pn.Column(ecg.pipeline))

    def __init__(self, main_page, **params):
        self.mainPage = main_page
        self.welcomeText = WELCOME_TEXT
        self.physBtn.on_click(self.start_physiological_pipeline)
        self.signalSelection.append(self.physBtn)
        super().__init__(**params)

    def view(self):
        return pn.Column(pn.pane.Markdown(self.welcomeText), self.signalSelection)

app = pn.template.BootstrapTemplate(
    title="BioPysKit Dashboard",
    header_background="#186FEF",
    logo="./assets/Icons/biopsykit_Icon.png",
)

app.config.console_output = "disable"
app.config.log_level = "CRITICAL"
app.sidebar.constant = False
app.main.constant = False
app.theme_toggle = False
current_page = MainPage(app.main)


def startPipeline(event):
    btn_name = event.obj.name
    if "Physiological" in btn_name:
        pipeline = PhysiologicalPipeline()
    # elif "Sleep" in btn_name:
    #     pipeline = SleepPipeline()
    # elif "Questionnaire" in btn_name:
    #     pipeline = QuestionnairePipeline()
    # elif "Saliva" in btn_name:
    #     pipeline = SalivaPipeline()
    # elif "Psychological" in btn_name:
    #     pipeline = PsychologicalPipeline()
    else:
        pn.state.notifications.error("No Pipeline found for this Button")
        return
    pane = pn.Column(
        pn.Row(
            pn.layout.HSpacer(),
            pipeline.pipeline.prev_button,
            pipeline.pipeline.next_button,
        ),
        pipeline.pipeline.stage,
        min_height=2000,
    )
    app.main[0].objects = [pane]


def get_sidebar():
    homeBtn = pn.widgets.Button(name="Home", button_type="primary")
    homeBtn.on_click(get_mainMenu)
    physBtn = pn.widgets.Button(name="Physiological Data")
    physBtn.on_click(startPipeline)
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    questionnaireBtn.on_click(startPipeline)
    psychBtn = pn.widgets.Button(name="Psychological Data")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    salBtn.on_click(startPipeline)
    column = pn.Column(homeBtn, physBtn, psychBtn, questionnaireBtn, salBtn, sleepBtn)
    return column


def get_mainMenu(event):
    fileString = """
        # Welcome to the BioPsyKit Dashboard

        ## Here you can analyse your Data using the BioPsyKit without any manual programming.

        Please select below one of the Signals you want to analyse. The corresponding guide will help you to get the best out of your data.

        """
    physBtn = pn.widgets.Button(
        name="Physiological Data",
        sizing_mode="stretch_width",
        align="end",
        button_type="primary",
    )
    physBtn.on_click(startPipeline)
    sleepBtn = pn.widgets.Button(
        name="Sleep Data",
        sizing_mode="stretch_width",
        align="end",
        button_type="primary",
    )
    sleepBtn.on_click(startPipeline)
    questionnaireBtn = pn.widgets.Button(
        name="Questionnaire Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    questionnaireBtn.on_click(startPipeline)
    psychBtn = pn.widgets.Button(
        name="Psychological Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    psychBtn.on_click(startPipeline)
    salBtn = pn.widgets.Button(
        name="Saliva Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    salBtn.on_click(startPipeline)
    if os.path.exists("./assets/Icons/"):
        pathToIcons = "./assets/Icons/"
    elif os.path.exists("../assets/Icons/"):
        pathToIcons = "../assets/Icons/"
    else:
        pathToIcons = "../../assets/Icons/"
    iconNames = [
        "Physiological.svg",
        "Psychological.svg",
        "Questionnaire.svg",
        "Saliva.svg",
        "Sleep.svg",
    ]
    physCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[0],
            align=("center"),
            sizing_mode="stretch_both",
            max_height=150,
            max_width=200,
            styles={"background": "whitesmoke"},
        ),
        pn.Spacer(height=45),
        physBtn,
        ncols=1,
        styles={"background": "whitesmoke", "align": "center"},
        width=250,
        height=250,
    )
    psychCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[1],
            align=("center"),
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            styles={"background": "whitesmoke"},
        ),
        pn.Spacer(height=45),
        psychBtn,
        ncols=1,
        styles={"background": "whitesmoke", "align": "center"},
        width=250,
        height=250,
    )
    questionnaireCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[2],
            align=("center"),
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            styles={"background": "whitesmoke"},
        ),
        pn.Spacer(height=45),
        questionnaireBtn,
        ncols=1,
        styles={"background": "whitesmoke", "align": "center"},
        width=250,
        height=250,
    )
    salCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[3],
            align=("center"),
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            styles={"background": "whitesmoke"},
        ),
        pn.Spacer(height=45),
        salBtn,
        ncols=1,
        styles={"background": "whitesmoke", "align": "center"},
        width=250,
        height=250,
    )
    sleepCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[4],
            align=("center"),
            sizing_mode="stretch_both",
            max_height=150,
            max_width=160,
            fixed_aspect=False,
        ),
        pn.Spacer(height=45),
        sleepBtn,
        ncols=1,
        styles={"background": "whitesmoke", "align": "center"},
        width=250,
        height=250,
    )
    signalSelection = pn.GridBox(
        *[physCard, psychCard, questionnaireCard, salCard, sleepCard],
        ncols=3,
        nrows=2,
        max_width=1000,
        height=600,
    )
    pane = pn.Column(pn.pane.Markdown(fileString), signalSelection)
    if len(app.main) > 0:
        app.main[0].objects = [pane]
    else:
        app.main.append(pane)


pn.config.console_output = "disable"
app.sidebar.append(get_sidebar())
get_mainMenu(None)
app.servable()


await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.globals.set('patch', msg.patch)
    self.pyodide.runPythonAsync(`
    state.curdoc.apply_json_patch(patch.to_py(), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.globals.set('location', msg.location)
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads(location)
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()