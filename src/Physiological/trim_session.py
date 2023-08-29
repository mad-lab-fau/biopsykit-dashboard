import panel as pn
import pandas as pd
import pytz

from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.utils import (
    timezone_aware_to_naive,
    get_datetime_columns_of_data_frame,
    get_start_and_end_time,
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
            "# Edit start and stop \n \n"
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
