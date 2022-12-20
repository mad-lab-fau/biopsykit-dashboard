from datetime import datetime
from typing import Tuple

import pandas as pd


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
