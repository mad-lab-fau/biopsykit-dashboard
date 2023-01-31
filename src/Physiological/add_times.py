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

from src.Physiological.data_arrived import DataArrived


class AskToAddTimes(DataArrived):
    text = ""
    ready = param.Boolean(default=True)
    next = param.Selector(
        default="Do you want to detect Outlier?",
        objects=["Do you want to detect Outlier?", "Add Times"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="Skip", button_type="success")
    add_times_btn = pn.widgets.Button(name="Add Phases", button_type="primary")

    def click_skip(self, event):
        self.next = "Do you want to detect Outlier?"
        self.ready = True

    def click_add_times(self, event):
        self.next = "Add Times"
        self.ready = True

    def panel(self):
        self.step = 5
        self.set_progress_value()
        if self.text == "":
            f = open("../assets/Markdown/AskToAddTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        self.add_times_btn.on_click(self.click_add_times)
        self.skip_btn.on_click(self.click_skip)
        return pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            pn.Row(self.add_times_btn, self.skip_btn),
        )


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
    subject_timestamps = []
    subj_time_dict = {}
    df = None

    def parse_time_file(self, event):
        df = None
        if ".csv" in self.time_upload.filename:
            string_io = StringIO(self.time_upload.value.decode("utf8"))
            df = pd.read_csv(string_io)
            self.handle_time_file(df)
        else:
            df = pd.read_excel(self.time_upload.value)
            df = self.handle_time_file(df)
            self.df = df
        if not self.ready:
            # Subject oder condition column nicht angegeben
            row = pn.Row()
            cols = list(self.df.columns)
            cols.insert(0, " ")
            slct_subject = pn.widgets.Select(name="Select Subject column", options=cols)
            slct_subject.link(
                "subject",
                callbacks={"value": self.subject_column_changed},
            )
            row.append(slct_subject)
            slct_condition = pn.widgets.Select(
                name="Select Condition column", options=cols
            )
            slct_condition.link(
                "condition",
                callbacks={"value": self.condition_column_changed},
            )
            row.append(slct_condition)
            self.pane.append(row)
            return
        if df is None:
            pn.state.notifications.error("Could not parse the given time File")
        self.df = df
        self.set_subject_time_dict()
        self.dict_to_column()

    def set_subject_time_dict(self):
        for subject_name in self.df.index:
            conditions = self.df.loc[subject_name]
            col = pn.Column()
            cond_name = conditions.condition
            self.subj_time_dict[subject_name] = {}
            self.subj_time_dict[subject_name][cond_name] = {}
            for dim in range(0, conditions.ndim):
                if conditions.ndim == 1:
                    condition = conditions.iloc[:]
                else:
                    condition = conditions.iloc[:, dim]
                for index, value in condition.items():
                    if isinstance(value, datetime.time):
                        self.subj_time_dict[subject_name][cond_name][
                            index
                        ] = datetime.datetime.combine(
                            datetime.datetime.now().date(),
                            value,
                        )
                    elif isinstance(value, str) and value.isalpha():
                        col.insert(
                            0,
                            pn.widgets.TextInput(
                                placeholder="Name the timestamp", value=value
                            ),
                        )

    def dict_to_column(self):
        timestamps = []
        for subject in self.subj_time_dict.keys():
            col = pn.Column()
            for condition in self.subj_time_dict[subject].keys():
                cond = pn.widgets.TextInput(value=condition)
                cond.link(
                    (subject, condition),
                    callbacks={"value": self.change_condition_name},
                )
                col.append(cond)
                for phase in self.subj_time_dict[subject][condition].keys():
                    row = pn.Row()
                    phase_name_input = pn.widgets.TextInput(value=phase)
                    phase_name_input.link(
                        (subject, condition, phase),
                        callbacks={"value": self.change_phase_name},
                    )
                    row.append(phase_name_input)
                    dt_picker = pn.widgets.DatetimePicker(
                        value=self.subj_time_dict[subject][condition][phase]
                    )
                    dt_picker.link(
                        (subject, condition, phase),
                        callbacks={"value": self.timestamp_changed},
                    )
                    row.append(dt_picker)
                    remove_btn = pn.widgets.Button(name="Remove", button_type="primary")
                    remove_btn.link(
                        (subject, condition, phase),
                        callbacks={"value": self.remove_btn_click},
                    )
                    row.append(remove_btn)
                    col.append(row)
                btn = pn.widgets.Button(name="Add Phase", button_type="primary")
                btn.link(
                    (subject, condition),
                    callbacks={"value": self.add_phase_btn_click},
                )
                col.append(btn)
                timestamps.append((subject, col))
        self.times.objects = [pn.Accordion(objects=timestamps)]

    def timestamp_changed(self, target, event):
        changed_timestamp = event.new
        self.subj_time_dict[target[0]][target[1]][target[2]] = changed_timestamp
        self.dict_to_column()

    def change_condition_name(self, target, event):
        self.subj_time_dict[target[0]][event.new] = self.subj_time_dict[target[0]].pop(
            target[1]
        )
        self.dict_to_column()

    def change_phase_name(self, target, event):
        self.subj_time_dict[target[0]][target[1]][event.new] = self.subj_time_dict[
            target[0]
        ][target[1]].pop(target[2])
        self.dict_to_column()

    def remove_btn_click(self, target, event):
        self.subj_time_dict[target[0]][target[1]].pop(target[2])
        self.dict_to_column()

    def add_timestamp(self, target, event):
        print(event)
        return

    def check_subject_condition_columns(self, df):
        if "subject" not in df.columns:
            pn.state.notifications.error("Subject column must be specified")
            return False
        if "condition" not in df.columns:
            pn.state.notifications.error("Condition column must be specified")
            return False
        return True

    def subject_column_changed(self, target, event):
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
        self.dict_to_column()

    def condition_column_changed(self, target, event):
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
        self.dict_to_column()

    def add_phase_btn_click(self, target, event):
        new_phase_name = "New Phase"
        if new_phase_name in self.subj_time_dict[target[0]][target[1]].keys():
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in self.subj_time_dict[target[0]][target[1]].keys():
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
        self.subj_time_dict[target[0]][target[1]][
            new_phase_name
        ] = datetime.datetime.now()
        self.dict_to_column()

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
            if not self.check_subject_condition_columns(df):
                self.ready = False
                return df
            subject_col = "subject"
            condition_col = "condition"
            df = df.set_index(subject_col)
            # df = df.groupby(condition_col).groups
            # is_subject_condition_dict(df)
            return df

    def panel(self):
        self.step = 6
        self.max_steps = 21
        self.set_progress_value()
        if self.text == "":
            f = open("../assets/Markdown/SelectTimes.md", "r")
            fileString = f.read()
            self.text = fileString
        self.progress.width_policy = "max"
        pn.bind(self.parse_time_file, self.time_upload.param.value, watch=True)
        self.add_button.on_click(self.add_timestamp)
        self.times = pn.Column(
            self.datetime[0][0], self.datetime[0][1], self.add_button
        )
        self.pane = pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
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
