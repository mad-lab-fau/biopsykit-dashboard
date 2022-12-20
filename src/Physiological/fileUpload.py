import biopsykit.io.nilspod
import param
import panel as pn
import pandas as pd
from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Physiological.sessionKind import SessionKind
from src.utils import get_datetime_columns_of_data_frame
from io import BytesIO
from io import StringIO
from typing import io
from nilspodlib import Session, SyncedSession


class FileUpload(SessionKind):
    text = ""
    filetype_Select = pn.widgets.Select(
        name="File Type", options=["Multi Session", "Single Session"]
    )
    file_input = pn.widgets.FileInput(
        background="WhiteSmoke", multiple=False, accept=".csv,.bin"
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

    @pn.depends("hardware_select.value", watch=True)
    def hardware_selection_changed(self):
        if self.hardware_select.value == "NilsPod":
            self.file_input.accept = ".csv,.bin"
        if self.hardware_select.value == "BioPac":
            self.file_input.accept = ".xslx,.xsl"

    @pn.depends("file_input.value", watch=True)
    def _parse_file_input(self):
        self.ready = False
        self.data = None
        value = self.file_input.value
        if value is not None or len(value) > 0:
            if type(self.file_input.value) == list and not self.synced:
                for val, fn in zip(self.file_input.value, self.file_input.filename):
                    self.handle_single_file(io.BytesIO(val), fn)
                self.data = Session(self.data)
                self.ready = True
            elif type(self.file_input.value) == list and self.synced:
                for val, fn in zip(self.file_input.value, self.file_input.filename):
                    self.handle_single_file(io.BytesIO(val), fn)
                self.data = SyncedSession(self.data)
                self.data = self.data.data_as_df()
                self.ready = True
            elif type(self.file_input.value) != list:
                self.handle_single_file(self.file_input.value, self.file_input.filename)
                if self.file_input.filename.endswith(".bin"):
                    (
                        self.data,
                        self.sampling_rate,
                    ) = biopsykit.io.nilspod.load_dataset_nilspod(dataset=self.data[0])
                self.ready = True
            else:
                pn.state.notifications.error("No matching operators")
        else:
            pn.state.notifications.error("No matching operators")

    def handle_single_file(self, value, filename):
        if filename.endswith(".bin"):
            self.handle_bin_file(bytefile=BytesIO(value))
            pn.state.notifications.success(filename)
        elif filename.endswith(".csv"):
            if self.file_input.filename.endswith(".csv"):
                self.handle_csv_file(bytefile=value)
        else:
            pn.state.notifications.error("Not a matching file format")

    def handle_bin_file(self, bytefile: bytes):
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=bytefile, legacy_support="resolve", tz=self.timezone
        )
        if self.data is None:
            self.data = []
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
        pn.state.notifications.success("File uploaded successfully", duration=5000)

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone)

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("synced", param.Boolean),
        ("session_type", param.String),
    )
    def output(self):
        return self.data, self.sampling_rate, self.synced, self.session_type

    def panel(self):
        if self.session_type == "Multi Session":
            self.file_input.multiple = True
        if self.text == "":
            f = open("../assets/Markdown/PhysiologicalFileUpload.md", "r")
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text), self.hardware_select, self.file_input
        )
