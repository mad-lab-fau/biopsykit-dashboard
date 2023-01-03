import biopsykit.io.nilspod
import param
import panel as pn
import pandas as pd
from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Physiological.session_kind import SessionKind
from src.utils import get_datetime_columns_of_data_frame
from io import BytesIO
from io import StringIO
from typing import io
from nilspodlib import SyncedSession
from src.utils import _handle_counter_inconsistencies_dataset
from biopsykit.utils.datatype_helper import *


class FileUpload(SessionKind):
    text = ""
    filetype_Select = pn.widgets.Select(
        name="File Type", options=["Multi Session", "Single Session"]
    )
    file_input = pn.widgets.FileInput(
        background="WhiteSmoke", multiple=True, accept=".csv,.bin,.xls,.xlsx"
    )
    session_type = param.String()
    synced = param.Boolean()
    timezone = param.String()
    ready = param.Boolean(default=False)
    data = None
    sampling_rate = param.Dynamic(default=-1)
    hardware_select = pn.widgets.Select(
        name="Select the Hardware with which you recorded your data",
        options=["NilsPod", "BioPac"],
        value="NilsPod",
    )
    phase_series = param.Dynamic()
    sensors = []
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()

    @pn.depends("hardware_select.value", watch=True)
    def hardware_selection_changed(self):
        if self.hardware_select.value == "NilsPod":
            self.file_input.accept = ".csv,.bin"
        if self.hardware_select.value == "BioPac":
            self.file_input.accept = ".acq"

    def parse_file_input(self, event):
        self.ready = False
        self.data = None
        if self.file_input.value is None or len(self.file_input.value) <= 0:
            pn.state.notifications.error("No Files arrived")
            return
        if type(self.file_input.value) != list:
            self.handle_single_session()
            return
        self.set_time_log()
        if (
            type(self.file_input.value) == list
            and len(self.file_input.value) <= 2
            and self.session_type == "Single Session"
        ):
            self.handle_single_session()
        elif type(self.file_input.value) == list and not self.synced:
            self.handle_multi_not_synced_sessions()
        elif type(self.file_input.value) == list and self.synced:
            self.handle_synced_sessions()

    def set_time_log(self):
        if not any(".xls" in name for name in self.file_input.filename):
            self.time_log_present = False
            return

        self.time_log_present = True
        indices = [
            i
            for i in range(len(self.file_input.filename))
            if ".xls" in self.file_input.filename[i]
        ]
        if len(indices) > 1:
            pn.state.notifications.error("More than one Excel File")
            self.time_log_present = False
            return
        self.time_log = pd.read_excel(self.file_input.value[indices[0]])

    # TODO: Das ist bei NilsPod gleich im DataSetType mit dabei
    def get_signal_type(self):
        if self.hardware_select.value == "NilsPod":
            self.sensors = "Test"
        if is_ecg_raw_dataframe(self.data, False):
            self.sensors = "ecg"
        elif is_gyr1d_dataframe(self.data, False):
            self.sensors = "eeg"

    def handle_single_session(self):
        for val, fn in zip(self.file_input.value, self.file_input.filename):
            if "xls" in fn:
                continue
            self.handle_single_file(val, fn)
            if fn.endswith(".bin"):
                (
                    self.data,
                    self.sampling_rate,
                ) = biopsykit.io.nilspod.load_dataset_nilspod(dataset=self.data[0])

            self.ready = True

    def handle_multi_not_synced_sessions(self):
        if self.data is dict:
            return
        session_names = [
            name.split(".")[0].split("_")[-1]
            for name in self.file_input.filename
            if "xls" not in name
        ]
        for val, fn in zip(self.file_input.value, self.file_input.filename):
            if "xls" in fn:
                continue
            self.handle_single_file(val, fn)
        dataset_dict = {vp: ds for vp, ds in zip(session_names, self.data)}
        self.sampling_rate = [
            ds.info.sampling_rate_hz for vp, ds in zip(session_names, self.data)
        ]
        if self.sampling_rate.count(self.sampling_rate[0]) != len(self.sampling_rate):
            pn.state.notifications.error("One sampling rate is different!")
            return
        self.sampling_rate = self.sampling_rate[0]
        self.data = dataset_dict
        self.ready = True

    def handle_synced_sessions(self):
        for val, fn in zip(self.file_input.value, self.file_input.filename):
            self.handle_single_file(val, fn)
        session = SyncedSession(self.data)
        session.align_to_syncregion(inplace=True)
        _handle_counter_inconsistencies_dataset(session, "ignore")
        df = session.data_as_df(None, index="local_datetime", concat_df=True)
        df.index.name = "time"
        if len(set(session.info.sampling_rate_hz)) > 1:
            raise ValueError(
                f"Datasets in the sessions have different sampling rates! Got: {session.info.sampling_rate_hz}."
            )
        fs = session.info.sampling_rate_hz[0]
        self.data = df
        self.sampling_rate = fs
        self.ready = True

    def handle_single_file(self, value, filename):
        if filename.endswith(".bin"):
            self.handle_bin_file(bytefile=BytesIO(value))
            pn.state.notifications.success(filename)
        elif filename.endswith(".csv"):
            self.handle_csv_file(bytefile=value)
        else:
            pn.state.notifications.error("Not a matching file format")

    def handle_bin_file(self, bytefile: bytes):
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=bytefile, legacy_support="resolve", tz=self.timezone
        )
        if self.data is None:
            self.data = []
        st = set(self.sensors)
        sensors = set(dataset.info.enabled_sensors)
        self.sensors = list(st.union(sensors))
        if type(self.data) is dict:
            return
        if dataset in self.data:
            return
        self.data.append(dataset)

    def handle_csv_file(self, bytefile: bytes):
        string_io = StringIO(bytefile.decode("utf8"))
        self.data = pd.read_csv(string_io, parse_dates=["time"])
        if self.data is None:
            pn.state.notifications.error("Empty csv File arrived", duration=10000)
        if "ecg" not in self.data.columns:
            pn.state.notifications.error(
                "Uploaded csv File misses the column ecg", duration=10000
            )
            return
        if "time" not in self.data.columns:
            pn.state.notifications.error(
                "Uploaded csv File misses the column time", duration=10000
            )
            return
        self.data["ecg"] = self.data["ecg"].astype(float)
        self.sensors.append("ecg")
        pn.state.notifications.success("File uploaded successfully", duration=5000)

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone)

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("synced", param.Boolean),
        ("session_type", param.String),
        ("sensors", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.time_log_present,
            self.time_log,
            self.synced,
            self.session_type,
            self.sensors,
        )

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/PhysiologicalFileUpload.md", "r")
            fileString = f.read()
            self.text = fileString
        pn.bind(self.parse_file_input, self.file_input.param.value, watch=True)
        return pn.Column(
            pn.pane.Markdown(self.text), self.hardware_select, self.file_input
        )
