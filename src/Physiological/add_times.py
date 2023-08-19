import datetime as datetime
from io import StringIO
import pandas as pd
import panel as pn
import param
from biopsykit.io.io import (
    _sanitize_index_cols,
)

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToAddTimes(PhysiologicalBase):
    data = param.Dynamic()
    sampling_rate = param.Number()
    skip_hrv = param.Boolean(default=True)
    session = param.String()
    sensors = param.Dynamic()
    timezone = param.String()
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    subject = param.Dynamic()

    text = ""
    ready = param.Boolean(default=False)
    next = param.Selector(
        default="Add Times",
        objects=["Do you want to detect Outlier?", "Add Times", "Frequency Bands"],
    )
    skip_btn = pn.widgets.Button(name="Skip", button_type="success")
    add_times_btn = pn.widgets.Button(name="Add Phases", button_type="primary")
    subject_time_dict = {}

    def __init__(self):
        super().__init__()
        self.step = 6
        text = (
            "# Do you want to add Phases for your Data?"
            "If you want to upload an Excel oder CSV File, or if you want to manually add Phases "
            "to your data then click on the Add Times Button otherwise skip"
        )
        self.set_progress_value(self.step)
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(self.progress))
        pane.append(pn.pane.Markdown(text))
        pane.append(pn.Row(self.add_times_btn, self.skip_btn))
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.add_times_btn.link(self, callbacks={"clicks": self.click_add_times})
        self.ready = False
        self._view = pane

    def click_skip(self, target, event):
        if self.selected_signal == "EEG":
            self.next = "Frequency Bands"
            self.ready = True
        else:
            self.next = "Do you want to detect Outlier?"
            self.ready = True

    def click_add_times(self, target, event):
        self.next = "Add Times"
        self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("timezone", param.String()),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.timezone,
        )

    def panel(self):
        return self._view


class AddTimes(PhysiologicalBase):
    data = param.Dynamic()
    sampling_rate = param.Number()
    skip_hrv = param.Boolean(default=True)
    session = param.String()
    sensors = param.Dynamic()
    timezone = param.String()
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    subject = param.Dynamic()
    subject_time_dict = {}

    time_upload = pn.widgets.FileInput(
        styles={"background": "whitesmoke"}, multiple=False, accept=".xls,.xlsx"
    )
    datetime = [
        (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.datetime.now()),
        )
    ]
    add_button = pn.widgets.Button(name="Add timestamp", button_type="danger")
    remove_button = pn.widgets.Button(name="Remove last Phase", button_type="danger")
    pane = pn.Column()
    time_log = None
    subject_log = None
    times = None
    subject_timestamps = []
    df = None
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )
    select_subject = pn.widgets.Select(name="Select Subject column", visible=False)
    select_condition = pn.widgets.Select(name="Select Condition column", visible=False)
    next = param.Selector(
        default="Do you want to detect Outlier?",
        objects=["Do you want to detect Outlier?", "Frequency Bands"],
    )
    freq_bands = {}

    def __init__(self):
        super().__init__()
        self.step = 6
        text = "# Select Times"
        self.time_upload.link(self, callbacks={"value": self.parse_time_file})
        self.add_button.link(self, callbacks={"clicks": self.add_timestamp})
        self.set_progress_value(self.step)
        self.times = pn.Column(
            self.datetime[0][0], self.datetime[0][1], self.add_button
        )
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(self.progress))
        pane.append(pn.pane.Markdown(text))
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
                self.times,
            )
        )
        pane.append(pn.Row(self.select_vp))
        pane.append(pn.Row(self.select_subject, self.select_condition))
        self._view = pane

    def panel(self):
        self.ready = False
        if self.selected_signal == "EEG":
            self.next = "Frequency Bands"
        self.init_subject_time_dict()
        self.dict_to_column()
        return self._view

    def parse_time_file(self, event):
        df = None
        self.ecg_processed = False
        self.select_condition.visible = False
        self.select_subject.visible = False
        self.select_vp.visible = False
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
            if "subject" not in self.df.columns:
                self.select_subject.options = cols
                self.select_subject.visible = True

                self.select_subject.link(
                    "subject",
                    callbacks={"value": self.subject_column_changed},
                )
            if "condition" not in self.df.columns:
                self.select_condition.options = cols
                self.select_condition.visible = True
                self.select_condition.link(
                    "condition",
                    callbacks={"value": self.condition_column_changed},
                )
            self.pane.append(row)
            return
        if df is None:
            pn.state.notifications.error("Could not parse the given time File")
            return
        self.df = df
        self.set_subject_time_dict()
        self.dict_to_column()

    def select_vp_changed(self, _, event):
        self.subject = event.new

    def set_subject_time_dict(self):
        for subject_name in self.df.index:
            conditions = self.df.loc[subject_name]
            cond_name = conditions.condition
            t_condition = conditions.drop(labels=["condition"])
            t_condition = t_condition.apply(
                lambda time: datetime.datetime.combine(
                    datetime.datetime.now().date(),
                    time,
                )
                if not isinstance(time, datetime.datetime)
                else time
            )
            self.subject_time_dict[subject_name] = {}
            self.subject_time_dict[subject_name][cond_name] = t_condition

    # def dict_to_column(self):
    #     if self.session == "Single Session" and len(self.subject_time_dict.keys()) > 1:
    #         self.select_vp.options = list(self.subject_time_dict.keys())
    #         self.select_vp.visible = True
    #         self.select_vp.link(
    #             "subject",
    #             callbacks={"value": self.select_vp_changed},
    #         )
    #         self.subject = list(self.subject_time_dict.keys())[0]
    #         self.ready = True
    #     timestamps = []
    #     for subject in self.subject_time_dict.keys():
    #         col = pn.Column()
    #         for condition in self.subject_time_dict[subject].keys():
    #             cond = pn.widgets.TextInput(value=condition)
    #             cond.link(
    #                 (subject, condition),
    #                 callbacks={"value": self.change_condition_name},
    #             )
    #             btn_remove_phase = pn.widgets.Button(
    #                 name="Remove Phase", button_type="danger"
    #             )
    #             btn_remove_phase.link(
    #                 (subject, condition),
    #                 callbacks={"value": self.remove_btn_click},
    #             )
    #             col.append(pn.Row(cond, btn_remove_phase))
    #             for phase, time in self.subject_time_dict[subject][condition].items():
    #                 row = pn.Row()
    #                 phase_name_input = pn.widgets.TextInput(value=phase)
    #                 phase_name_input.link(
    #                     (subject, condition, phase),
    #                     callbacks={"value": self.change_phase_name},
    #                 )
    #                 row.append(phase_name_input)
    #                 dt_picker = pn.widgets.DatetimePicker(value=time)
    #                 dt_picker.link(
    #                     (subject, condition, phase),
    #                     callbacks={"value": self.timestamp_changed},
    #                 )
    #                 row.append(dt_picker)
    #                 remove_btn = pn.widgets.Button(name="Remove", button_type="danger")
    #                 remove_btn.link(
    #                     (subject, condition, phase),
    #                     callbacks={"value": self.remove_btn_click},
    #                 )
    #                 row.append(remove_btn)
    #                 col.append(row)
    #             btn_subphase = pn.widgets.Button(
    #                 name="Add Subphase", button_type="primary"
    #             )
    #             btn_subphase.link(
    #                 (subject, condition),
    #                 callbacks={"value": self.add_subphase_btn_click},
    #             )
    #             row = pn.Row(pn.layout.HSpacer(), pn.layout.HSpacer(), btn_subphase)
    #             col.append(row)
    #         btn = pn.widgets.Button(name="Add Phase", button_type="primary")
    #         btn.link(
    #             (subject,),
    #             callbacks={"value": self.add_phase_btn_click},
    #         )
    #         col.append(btn)
    #         timestamps.append((subject, col))
    #     self.times.objects = [pn.Accordion(objects=timestamps)]

    def timestamp_changed(self, target, event):
        changed_timestamp = event.new
        self.subject_time_dict[target[0]][target[1]].loc[target[2]] = changed_timestamp
        self.dict_to_column()

    def change_condition_name(self, target, event):
        self.subject_time_dict[target[0]][event.new] = self.subject_time_dict[
            target[0]
        ].pop(target[1])
        self.dict_to_column()

    def change_phase_name(self, target, event):
        self.subject_time_dict[target[0]][target[1]].rename(
            {target[2]: event.new}, inplace=True
        )
        self.dict_to_column()

    def remove_btn_click(self, target, event):
        if len(target) == 3:
            self.subject_time_dict[target[0]][target[1]].drop(
                labels=target[2], inplace=True
            )
        elif len(target) == 2:
            self.subject_time_dict[target[0]].pop(target[1])
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

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
        self.select_condition.visible = False
        self.dict_to_column()

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
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("timezone", param.String()),
        ("subject_time_dict", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.timezone,
            self.subject_time_dict,
        )
