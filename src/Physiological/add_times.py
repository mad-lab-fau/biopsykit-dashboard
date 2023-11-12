from datetime import datetime
from io import StringIO
import pandas as pd
import panel as pn
import param
from biopsykit.io.io import (
    _sanitize_index_cols,
)

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import ADD_TIMES_TEXT, ASK_ADD_TIMES_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.custom_components import TimesToSubject


class AskToAddTimes(PhysiologicalBase):
    ready = param.Boolean(default=False)
    next = param.Selector(
        default="Add Times",
        objects=["Do you want to detect Outlier?", "Add Times", "Frequency Bands"],
    )
    skip_btn = pn.widgets.Button(
        name="Skip", button_type="default", sizing_mode="stretch_width"
    )
    add_times_btn = pn.widgets.Button(
        name="Add Phases", button_type="primary", sizing_mode="stretch_width"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_ADD_TIMES_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.add_times_btn.link(self, callbacks={"clicks": self.click_add_times})
        self.ready = False
        pane = pn.Column(self.header)
        pane.append(pn.Row(self.add_times_btn, self.skip_btn))
        self._view = pane

    def click_skip(self, _, event):
        if self.signal == "EEG":
            self.next = "Frequency Bands"
            self.ready = True
        else:
            self.next = "Do you want to detect Outlier?"
            self.ready = True

    def click_add_times(self, _, event):
        self.next = "Add Times"
        self.ready = True

    def panel(self):
        return self._view


class AddTimes(PhysiologicalBase):
    time_upload = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".xls,.xlsx,.csv",
        align="end",
    )
    datetime = [
        (
            pn.widgets.TextInput(placeholder="Name the timestamp"),
            pn.widgets.DatetimePicker(value=datetime.now()),
        )
    ]
    subject_log = None
    subject_timestamps = []
    df = None
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )
    next = param.Selector(
        default="Do you want to detect Outlier?",
        objects=["Do you want to detect Outlier?", "Frequency Bands"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ADD_TIMES_TEXT
        self.ready = False
        super().__init__(**params)
        self.update_step(6)
        self.time_upload.link(self, callbacks={"filename": self.parse_time_file})
        self.times_to_subject = TimesToSubject([])
        self.select_subject = pn.widgets.Select(
            name="Select Subject column", visible=False
        )
        self.select_condition = pn.widgets.Select(
            name="Select Condition column", visible=False
        )
        self.select_condition.link(
            self,
            callbacks={"value": self.condition_column_changed},
        )
        self.select_subject.link(
            self,
            callbacks={"value": self.subject_column_changed},
        )
        pane = pn.Column(self.header)
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
                self.times_to_subject,
            )
        )
        pane.append(pn.Row(self.select_vp))
        pane.append(pn.Row(self.select_subject, self.select_condition))
        self.ready = self.times_to_subject.is_ready()
        self._view = pane

    def panel(self):
        if self.signal == "EEG":
            self.next = "Frequency Bands"
        self.times_to_subject.initialize_filenames(list(self.data.keys()))
        return self._view

    def parse_time_file(self, target, event):
        if self.time_upload.value is None:
            return
        self.select_condition.visible = False
        self.select_subject.visible = False
        self.select_vp.visible = False
        self.df = self.parse_file(self.time_upload.filename, self.time_upload.value)
        if self.df is None:
            pn.state.notifications.error("Could not parse the given time File")
            return
        if not self.ready:
            self.ask_for_additional_infos()
            return
        self.set_subject_time_dict()

    def ask_for_additional_infos(self):
        # row = pn.Row()
        cols = list(self.df.columns)
        cols.insert(0, " ")
        if "subject" not in self.df.columns:
            self.select_subject.options = cols
            self.select_subject.visible = True
        if "condition" not in self.df.columns:
            self.select_condition.options = cols
            self.select_condition.visible = True
        # self.pane.append(row)

    def parse_file(self, file_name, file_content) -> pd.DataFrame:
        if file_content is None:
            pn.state.notifications.error("No file content")
            return pd.DataFrame()
        if ".csv" in file_name:
            string_io = StringIO(file_content.decode("utf8"))
            df = pd.read_csv(string_io)
        else:
            df = pd.read_excel(file_content)
        df = self.handle_time_file(df)
        return df

    def select_vp_changed(self, _, event):
        self.subject = event.new

    def set_subject_time_dict(self):
        for subject_name in self.df.index:
            conditions = self.df.loc[subject_name]
            cond_name = conditions.condition
            t_condition = conditions.drop(labels=["condition"])
            t_condition = t_condition.apply(
                lambda time: datetime.combine(
                    datetime.now().date(),
                    time,
                )
                if not isinstance(time, datetime)
                else time
            )
            self.subject_time_dict[subject_name] = {}
            self.subject_time_dict[subject_name][cond_name] = t_condition
        self.times_to_subject.add_new_subject_time_dict(self.subject_time_dict)

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

    def condition_column_changed(self, _, event):
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
        ("freq_bands", param.Dynamic),
        ("synced", param.Boolean),
        ("subject_time_dict", param.Dynamic),
        ("timezone", param.String()),
        ("trimmed_data", param.Dynamic),
        ("session", param.String),
        ("selected_signal", param.String),
        ("recording", param.String),
        ("data", param.Dynamic),
        ("sampling_rate", param.Number),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Boolean),
        ("time_log", param.Dynamic),
        ("outlier_params", param.Dynamic),
        ("selected_outlier_methods", param.Dynamic),
        ("skip_hrv", param.Boolean),
        ("subject", param.Dynamic),
        ("cft_sheets", param.Dynamic),
        ("phase_series", param.Dynamic),
    )
    def output(self):
        file_dict = self.times_to_subject.get_files_to_subjects()
        subject_time_dict = self.times_to_subject.get_subject_time_dict()
        for file_name in file_dict.keys():
            if file_name not in self.data.keys():
                continue
            self.data[file_dict[file_name]] = self.data.pop(file_name)
        self.subject_time_dict = subject_time_dict
        return (
            self.freq_bands,
            self.synced,
            self.subject_time_dict,
            self.timezone,
            self.trimmed_data,
            self.session,
            self.signal,
            self.recording,
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.get_outlier_params(),
            self.outlier_methods,
            self.skip_hrv,
            self.subject,
            self.cft_sheets,
            self.phase_series,
        )
