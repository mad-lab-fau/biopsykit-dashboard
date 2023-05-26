import datetime
import re
import string
import zipfile
from zipfile import ZipFile

import biopsykit.io.nilspod
import param
import panel as pn
import pandas as pd
import pytz
from biopsykit.io.eeg import MuseDataset
from biopsykit.utils.datatype_helper import HeartRatePhaseDict

from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Physiological.recordings import Recordings
from src.utils import get_datetime_columns_of_data_frame
from io import BytesIO
from io import StringIO
from nilspodlib import SyncedSession
from src.utils import _handle_counter_inconsistencies_dataset


class FileUpload(Recordings):
    text = ""
    filetype_Select = pn.widgets.Select(
        name="File Type", options=["Multi Session", "Single Session"]
    )
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xls,.xlsx",
    )
    session_type = param.Dynamic()
    synced = param.Boolean()
    timezone_select = pn.widgets.Select(
        name="Timezone",
        options=["None Selected"] + list(pytz.all_timezones),
        value="Europe/Berlin",
    )
    data = pd.DataFrame()
    hr_data = None
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
    data_processed = False

    @pn.depends("hardware_select.value", watch=True)
    def hardware_selection_changed(self):
        if self.hardware_select.value == "NilsPod":
            self.file_input.accept = ".csv,.bin, .zip"
        if self.hardware_select.value == "BioPac":
            self.file_input.accept = ".acq"

    def parse_file_input(self, event):
        if self.data is None:
            self.ready = False
        self.data = None
        self.ecg_processed = False
        if self.file_input.value is None or len(self.file_input.value) <= 0:
            pn.state.notifications.error("No Files arrived")
            return
        if ".zip" in self.file_input.filename:
            # Daten noch entpacken und dann parsen
            self.extract_zip(self.file_input.value)
            pn.state.notifications.success("unzipped")
            return
        else:
            # Eine Session dann mit einem oder mehreren Sensoren
            fileType = self.file_input.filename[
                self.file_input.filename.rindex(".") + 1 :
            ]
            match fileType:
                case "csv":
                    self.handle_csv_file(bytefile=self.file_input.value)
                    return
                case "bin":
                    self.handle_bin_file(bytefile=self.file_input.value)
                    return
                case "xlsx":
                    self.handle_xlsx_file(
                        bytefile=self.file_input.value,
                        filename=self.file_input.filename,
                    )
                case _:
                    pn.state.notifications.error("No matching parser found")
        return

    def extract_zip(self, input_zip):
        input_zip = ZipFile(BytesIO(input_zip))
        datasets = []
        path = zipfile.Path(input_zip)
        subject_data_dict = {}
        for file_path in path.iterdir():
            if file_path.name.startswith("__"):
                continue
            if file_path.is_dir():
                subject_id = file_path.name
                ds = []
                for file in file_path.iterdir():
                    if ".bin" in file.name:
                        dataset = NilsPodAdapted.from_bin_file(
                            filepath_or_buffer=BytesIO(input_zip.read(file.at)),
                            legacy_support="resolve",
                            tz=self.timezone_select.value,
                        )
                        ds.append(dataset)
                subject_data_dict[subject_id] = ds
            elif ".bin" in file_path.name:
                subject_id = file_path.name.split(".")[0].split("_")[-1]
                dataset = NilsPodAdapted.from_bin_file(
                    filepath_or_buffer=BytesIO(input_zip.read(file_path.name)),
                    legacy_support="resolve",
                    tz=self.timezone_select.value,
                )
                datasets.append(dataset)
                subject_data_dict[subject_id] = {}
        # for name in input_zip.namelist():
        #     if name.startswith("__"):
        #         continue
        #     subject_id = name.split(".")[0].split("_")[-1]
        #     if ".bin" in name:
        #         dataset = NilsPodAdapted.from_bin_file(
        #             filepath_or_buffer=BytesIO(input_zip.read(name)),
        #             legacy_support="resolve",
        #             tz=self.timezone_select.value,
        #         )
        #         datasets.append(dataset)
        try:
            subject_synced = {}
            for subject in subject_data_dict.keys():
                synced = SyncedSession(datasets)
                synced.align_to_syncregion(inplace=True)
                _handle_counter_inconsistencies_dataset(synced, "ignore")
                df = synced.data_as_df(None, index="local_datetime", concat_df=True)
                df.index.name = "time"
                if len(set(synced.info.sampling_rate_hz)) > 1:
                    raise ValueError(
                        f"Datasets in the sessions have different sampling rates! Got: {synced.info.sampling_rate_hz}."
                    )
                fs = synced.info.sampling_rate_hz[0]
                subject_synced[subject] = df
            self.data = subject_synced
            self.sampling_rate = fs
            self.ready = True
        except Exception as e:
            pn.state.notifications.warning("Could not sync data")
            subject_phase_data_dict = {}
            for subject in subject_data_dict.keys():
                dataset_list = [
                    biopsykit.io.nilspod.load_dataset_nilspod(dataset=dataset)
                    for dataset in subject_data_dict[subject]
                ]
                fs_list = [fs for df, fs in dataset_list]
                df_all = pd.concat([df for df, fs in dataset_list], axis=0)
                self.sampling_rate = fs_list[0]
                # phase_names = [f"Part{i}" for i in range(len(dataset_list))]
                # dataset_dict = {
                #     phase: df for phase, (df, fs) in zip(phase_names, dataset_list)
                # }
                # subject_phase_data_dict[subject] = dataset_dict
                subject_phase_data_dict[subject] = df_all
            self.data = subject_phase_data_dict
            self.ready = True

    def handle_single_session(self):
        for val, fn in zip(self.file_input.value, self.file_input.filename):
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
        dataset_dict = {
            vp: self.dataset_to_df(ds) for vp, ds in zip(session_names, self.data)
        }
        self.sampling_rate = [
            ds.info.sampling_rate_hz for vp, ds in zip(session_names, self.data)
        ]
        if self.sampling_rate.count(self.sampling_rate[0]) != len(self.sampling_rate):
            pn.state.notifications.error("One sampling rate is different!")
            return
        self.sampling_rate = self.sampling_rate[0]
        self.data = dataset_dict
        self.ready = True

    def dataset_to_df(self, ds):
        df = ds.data_as_df()
        start = ds.info.utc_datetime_start
        sr = ds.info.sampling_rate_hz
        step = datetime.timedelta(seconds=1 / sr)
        my_ind = [start]
        for i in range(len(df) - 1):
            c = my_ind[i]
            x = my_ind[i] + step
            my_ind.append(x)
        a = pd.Index(my_ind)
        df.set_index(a, inplace=True)
        df.index.name = "index"
        return df

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

    def handle_xlsx_file(self, bytefile: bytes, filename: string):
        if self.selected_signal == "CFT" and filename.endswith(".xlsx"):
            dict_hr: HeartRatePhaseDict = pd.read_excel(
                BytesIO(bytefile), index_col="time", sheet_name=None
            )
            dict_hr = {
                k: v.tz_localize(self.timezone_select.value) for k, v in dict_hr.items()
            }
            self.data = dict_hr
        if filename.endswith(".xlsx") and "hr_result" in filename:
            subject_id = re.findall("hr_result_(Vp\w+).xlsx", filename)[0]
            hr = pd.read_excel(BytesIO(bytefile), sheet_name=None, index_col="time")
            self.hr_data[subject_id] = hr
        pn.state.notifications.success("File uploaded successfully", duration=5000)
        self.ready = True

    def handle_bin_file(self, bytefile: bytes):
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=BytesIO(bytefile),
            legacy_support="resolve",
            tz=self.timezone_select.value,
        )
        st = set(self.sensors)
        sensors = set(dataset.info.enabled_sensors)
        self.sensors = list(st.union(sensors))
        df, fs = biopsykit.io.nilspod.load_dataset_nilspod(dataset=dataset)
        self.sampling_rate = fs
        self.data = df
        self.ready = True

    def handle_csv_file(self, bytefile: bytes):
        string_io = StringIO(bytefile.decode("utf8"))
        self.data = pd.read_csv(string_io)  # , parse_dates=["time"]
        if self.selected_signal == "EEG":
            self.data = MuseDataset(data=self.data, tz=self.timezone_select.value)
        else:
            for col in self.data.columns:
                if "timestamp" in col.lower():
                    try:
                        self.data[col] = pd.Timestamp(self.data[col])
                        self.data.set_index(col, inplace=True)
                    except ValueError:
                        pass
                if "time" in col.lower():
                    try:
                        self.data[col] = pd.to_datetime(self.data[col])
                        self.data.set_index(col, inplace=True)
                    except ValueError:
                        pass
        if self.data is None:
            pn.state.notifications.error("Empty csv File arrived", duration=10000)
        # if "ecg" not in self.data.columns:
        #     pn.state.notifications.error(
        #         "Uploaded csv File misses the column ecg", duration=10000
        #     )
        #     return
        # if "time" not in self.data.columns:
        #     pn.state.notifications.error(
        #         "Uploaded csv File misses the column time", duration=10000
        #     )
        #     return
        # self.data["ecg"] = self.data["ecg"].astype(float)
        # self.sensors.append("ecg")
        pn.state.notifications.success("File uploaded successfully", duration=5000)
        self.ready = True

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone_select.value)

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("synced", param.Boolean),
        ("session_type", param.String),
        ("sensors", param.Dynamic),
        ("timezone", param.Dynamic),
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
            self.timezone_select.value,
        )

    def panel(self):
        self.step = 3
        if self.recording.value == "Multiple Recording":
            self.file_input.accept = ".zip"
        else:
            self.file_input.accept = ".csv,.bin,.xls,.xlsx"
        if self.text == "":
            f = open("../assets/Markdown/PhysiologicalFileUpload.md", "r")
            fileString = f.read()
            self.text = fileString
        pn.bind(self.parse_file_input, self.file_input.param.value, watch=True)
        if self.data is not None:
            self.ready = True
        else:
            self.ready = False
        self.set_progress_value()
        return pn.Column(
            pn.pane.Markdown(self.text),
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            self.hardware_select,
            self.timezone_select,
            self.file_input,
        )
