from datetime import datetime

import pandas as pd


def get_datetime_columns_of_data_frame(df: pd.DataFrame):
    df_type = df.dtypes.rename_axis('column') \
        .to_frame('dtype') \
        .reset_index(drop=False)
    df_type['dtype_str'] = df_type['dtype'].map(str)
    return df_type[df_type['dtype_str'].str.contains('datetime64')]['column'].tolist()


def timezone_aware_to_naive(dt: datetime) -> datetime:
    naive = datetime(
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        second=dt.second,
        tzinfo=None)
    return naive
