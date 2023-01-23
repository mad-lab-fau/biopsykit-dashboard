import datetime as datetime
from io import StringIO
from typing import Optional, Union, Sequence, Tuple

import numpy as np
import pandas as pd
import panel as pn
import param
from biopsykit.io.io import (
    _get_subject_col,
    _sanitize_index_cols,
    _apply_index_cols,
    _parse_time_log_not_continuous,
)
from biopsykit.utils._datatype_validation_helper import (
    _assert_is_dtype,
)

from src.Physiological.file_upload import FileUpload


class AskToAddTimes(FileUpload):
    text = ""
    ready = param.Boolean(default=True)
    next = param.Selector(
        default="Want to correct Outlier?",
        objects=["Want to correct Outlier?", "Add Times"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="Skip", button_type="success")
    add_times_btn = pn.widgets.Button(name="Add Phases", button_type="primary")

    def click_skip(self, event):
        self.next = "Want to correct Outlier?"
        self.ready = True

    def click_add_times(self, event):
        self.next = "Add Times"
        self.ready = True

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/AskToAddTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        self.add_times_btn.on_click(self.click_add_times)
        self.skip_btn.on_click(self.click_skip)
        return pn.Column(
            pn.Row(self.step, self.progress),
            pn.pane.Markdown(self.text),
            pn.Row(self.add_times_btn, self.skip_btn),
        )


# TODO: Checkboxes für VPs (wenn mehrere VPs angegeben werden), Select für: subject_col und condition_col (nur wenn es fehl schlägt), für VP (wenn man nur eine will)
class AddTimes(AskToAddTimes):
    time_upload = pn.widgets.FileInput(
        background="WhiteSmoke", multiple=False, accept=".xls,.xlsx"
    )
    datetime = [
        (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.datetime.now()),
        )
    ]
    add_button = pn.widgets.Button(name="Add timestamp", button_type="danger")
    remove_button = pn.widgets.Button(name="Remove last Phase")
    pane = pn.Column()
    time_log = None
    subject_log = None
    times = None

    # TODO: Verbindung zwischen Remove und dem richtigen Ort
    def parse_time_file(self, event):
        df = None
        if ".csv" in self.time_upload.filename:
            string_io = StringIO(self.time_upload.value.decode("utf8"))
            df = pd.read_csv(string_io)
            self.handle_time_file(df)
        else:
            df = pd.read_excel(self.time_upload.value)
            df = self.handle_time_file(df)

        if df is None:
            pn.state.notifications.error("Could not parse the given time File")
        uploaded_times = pn.Accordion()
        # Wenn Multiple Sessions -> VP -> List of Tuple(Condition -> Time)

        for subject_name in df.index:
            conditions = df.loc[subject_name]
            person = (subject_name,)
            col = pn.Column()
            for dim in range(0, conditions.ndim):
                condition = None
                if conditions.ndim == 1:
                    condition = conditions.iloc[:]
                else:
                    condition = conditions.iloc[:, dim]
                cond_times = []
                for index, value in condition.items():
                    if isinstance(value, datetime.time):
                        row = pn.Row()
                        row.append(pn.widgets.StaticText(value=index))
                        t = datetime.datetime.combine(
                            datetime.datetime.now().date(), value
                        )
                        row.append(pn.widgets.DatetimePicker(value=t))
                        row.append(pn.widgets.Button(name="Remove Timestamp"))
                        col.append(row)
                    elif isinstance(value, str) and value.isalpha():
                        col.insert(
                            0,
                            pn.widgets.TextInput(
                                placeholder="Name the timestamp", value=value
                            ),
                        )
            btn = pn.widgets.Button(name="Add Timestamp", button_type="primary")
            btn.on_click(self.add_timestamp)
            col.append(btn)
            person = (subject_name, col)
            uploaded_times.append(person)
        self.times.objects = [uploaded_times]

    def add_timestamp(self, event):
        print(event)
        return

    def handle_time_file(self, df):
        if self.session.value == "Single Session":
            df, index_cols = _sanitize_index_cols(df, _get_subject_col(df), None, None)
            data = _apply_index_cols(df, index_cols=index_cols)
            data.columns.name = "phase"
            data = _parse_time_log_not_continuous(data, index_cols)
            for val in data.values.flatten():
                if val is np.nan:
                    continue
                _assert_is_dtype(val, str)
            return data
        else:
            subject_col = "subject"
            condition_col = "condition"
            df = df.set_index(subject_col)
            # df = df.groupby(condition_col).groups
            # is_subject_condition_dict(df)
            return df

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/SelectTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.progress.value = 5
        self.step.value = "Step 4 of " + str(self.max_steps)
        self.progress.width_policy = "max"
        pn.bind(self.parse_time_file, self.time_upload.param.value, watch=True)
        self.add_button.on_click(self.add_timestamp)
        self.times = pn.Column(
            self.datetime[0][0], self.datetime[0][1], self.add_button
        )

        self.pane = pn.Column(
            pn.Row(self.step, self.progress),
            pn.pane.Markdown(self.text),
            pn.widgets.StaticText(
                name="Add Times",
                value="Here you can add Time sections manually or you can upload an Excel File",
            ),
            pn.Row(
                self.time_upload,
                self.times,
            ),
        )
        return self.pane
