import datetime
import param
import panel as pn
import pandas as pd

from src.Physiological.process_hrv import SetHRVParameters

# TODO: hier sollte es unterscheidung zwischen
class SelectTimes(SetHRVParameters):
    text = ""
    datetime = [
        (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.datetime.now()),
        )
    ]
    add_button = pn.widgets.Button(name="Add timestamp")
    remove_button = pn.widgets.Button(name="Remove last Phase")
    pane = pn.Column()

    @param.output(
        ("session", param.Dynamic),
        ("synced", param.Boolean),
        ("timezone", param.String),
        ("phase_series", param.Dynamic),
    )
    def output(self):
        time_list = []
        name_list = []
        for name_time in self.datetime:
            name_list.append(name_time[0].value)
            time_list.append(name_time[1].value.strftime("%H:%M"))
        self.phase_series = pd.Series(time_list, index=name_list)
        super().output()

    def add_time(self, event):
        name_time = (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.datetime.now()),
        )
        self.datetime.append(name_time)
        self.pane.append(name_time[0])
        self.pane.append(name_time[1])

    def remove_time(self, event):
        if len(self.datetime) <= 0:
            return
        self.datetime.pop()
        self.pane.pop(-1)
        self.pane.pop(-1)

    def panel(self, f=None):
        if len(self.pane) > 0:
            return self.pane
        if self.text == "":
            f = open("../assets/Markdown/SelectTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        self.pane.append(pn.pane.Markdown(self.text))
        self.add_button.on_click(self.add_time)
        self.pane.append(self.add_button)
        self.remove_button.on_click(self.remove_time)
        self.pane.append(self.remove_button)
        for name_time in self.datetime:
            self.pane.append(name_time[0])
            self.pane.append(name_time[1])
        return self.pane
