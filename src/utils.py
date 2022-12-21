import warnings
from datetime import datetime
from typing import Tuple

import biopsykit
import numpy as np
import pandas as pd
from nilspodlib import Dataset
from typing_extensions import Literal

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
