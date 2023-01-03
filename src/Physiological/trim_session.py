import param
import panel as pn
import pandas as pd
import pytz
from src.utils import (
    timezone_aware_to_naive,
    get_datetime_columns_of_data_frame,
    get_start_and_end_time,
)


class TrimSession(param.Parameterized):
    original_data = param.Dynamic()
    trimmed_data = param.Dynamic()
    sampling_rate = param.Dynamic()
    text = ""
    start_time = pn.widgets.DatetimePicker(name="Start time")
    stop_time = pn.widgets.DatetimePicker(name="Stop time")
    trim_btn = pn.widgets.Button(name="Trim", button_type="primary")
    min_time = None
    max_time = None
    sensors = param.Dynamic()
    time_log = param.Dynamic()
    time_log_present = param.Boolean()

    def limit_times(self):
        if type(self.original_data) is pd.DataFrame:
            start_end = get_start_and_end_time(self.original_data)
            if start_end is None:
                return
            self.min_time = timezone_aware_to_naive(start_end[0])
            self.max_time = timezone_aware_to_naive(start_end[1])
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

    def trim_data(self, event):
        print("Trim started")
        print(self.trim_btn.clicks)
        if type(self.original_data) is pd.DataFrame:
            print("trim df")
            dt_col = get_datetime_columns_of_data_frame(self.original_data)
            if len(dt_col) == 1:
                col = dt_col[0]
                start = self.start_time.value
                stop = self.stop_time.value
                tz = pytz.timezone("Europe/Berlin")
                start = tz.localize(start)
                stop = tz.localize(stop)
                self.trimmed_data = self.original_data.loc[
                    (self.original_data[col] >= start)
                    & (self.original_data[col] <= stop)
                ]
        else:
            print("session")

    def panel(self):
        self.trim_btn.on_click(self.trim_data)
        self.trimmed_data = self.original_data
        self.limit_times()
        if self.text == "":
            f = open("../assets/Markdown/EditStartAndStopTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.start_time,
            self.stop_time,
            self.trim_btn,
        )

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
    )
    def output(self):
        return (
            self.trimmed_data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
        )
