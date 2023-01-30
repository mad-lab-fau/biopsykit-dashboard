import warnings
from datetime import datetime
from io import BytesIO
from typing import Tuple, Optional, Union, Sequence, Dict
from zipfile import ZipFile

from biopsykit.io.nilspod import _handle_counter_inconsistencies_session
from biopsykit.utils._datatype_validation_helper import _assert_file_extension
from biopsykit.utils.time import tz

import panel as pn
import biopsykit
import numpy as np
import pandas as pd
from nilspodlib import Dataset, SyncedSession
from typing_extensions import Literal

from src.Physiological.AdaptedNilspod import SyncedSessionAdapted, NilsPodAdapted

COUNTER_INCONSISTENCY_HANDLING = Literal["raise", "warn", "ignore"]


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
    zipFile: Optional[ZipFile] = None,
    file_path: Optional[str] = None,
    dataset: Optional[Dataset] = None,
    datastreams: Optional[Union[str, Sequence[str]]] = None,
    handle_counter_inconsistency: Optional[COUNTER_INCONSISTENCY_HANDLING] = "raise",
    **kwargs,
) -> Tuple[pd.DataFrame, float]:
    if zipFile is not None:
        _assert_file_extension(file_path, ".bin")
        kwargs.setdefault("tz", kwargs.pop("timezone", tz))
        kwargs.setdefault("legacy_support", "resolve")
        dataset = NilsPodAdapted.from_bin_file(
            BytesIO(zipFile.read(file_path)), **kwargs
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
        load_dataset_nilspod_zip(file_path=dataset_path, zipFile=file, **kwargs)
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
