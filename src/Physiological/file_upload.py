import re
import string
import zipfile
from typing import Tuple, List, Dict
from zipfile import ZipFile
import biopsykit as bp
import param
import panel as pn
import pandas as pd
import pytz
from biopsykit.io.eeg import MuseDataset
from biopsykit.utils.datatype_helper import HeartRatePhaseDict
from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.utils import get_datetime_columns_of_data_frame
from io import BytesIO
from io import StringIO
from nilspodlib import SyncedSession, Dataset
from src.utils import _handle_counter_inconsistencies_dataset


class FileUpload(PhysiologicalBase):
    selected_signal = param.String()
    session = param.Dynamic()
    recording = param.String()
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xlsx",
    )
    synced = param.Boolean()
    timezone = param.Selector(
        default="Europe/Berlin",
        objects=["None Selected"] + list(pytz.all_timezones),
        label="Timezone",
    )
    data = pd.DataFrame()
    hr_data = None
    sampling_rate = param.Dynamic(default=-1)
    hardware = param.Selector(
        label="Select the Hardware with which you recorded your data",
        objects=["NilsPod", "BioPac"],
        default="NilsPod",
    )
    phase_series = param.Dynamic()
    sensors = []
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()

    def __init__(self):
        super().__init__()
        self.ready = param.Boolean(default=False)
        self.step = 4
        self._select_timezone = pn.widgets.Select.from_param(self.param.timezone)
        pn.bind(self.timezone_changed, self._select_timezone.value, watch=True)
        self._select_hardware = pn.widgets.Select.from_param(self.param.hardware)
        pn.bind(self.hardware_changed, self._select_hardware.value, watch=True)
        self.text = (
            "# Upload your session File \n"
            "## The supported File formats are .bin, .csv, and you can also choose Folders.\n"
            "After your upload your file will also be checked if it contains the necessary columns.\n"
        )
        pn.bind(self.parse_file_input, self.file_input.param.value, watch=True)
        self._view = pn.Column(
            pn.pane.Markdown(self.text),
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.get_progress(self.step)),
            self._select_hardware,
            self._select_timezone,
            self.file_input,
        )

    @param.depends("timezone", watch=True)
    def timezone_changed(self):
        if self.timezone == "None Selected":
            self.ready = False
        else:
            self.ready = True

    @param.depends("hardware", watch=True)
    def hardware_changed(self):
        if self.hardware == "NilsPod":
            self.file_input.accept = ".csv,.bin, .zip"
        if self.hardware == "BioPac":
            self.file_input.accept = ".acq"

    def parse_file_input(self, _):
        self.ready = self.data is not None
        self.data = None
        if self.file_input.value is None or len(self.file_input.value) <= 0:
            pn.state.notifications.error("No Files arrived")
            return
        if self.file_input.filename is None or "." not in self.file_input.filename:
            pn.state.notifications.error("No Files arrived")
            return
        fileType = self.file_input.filename[self.file_input.filename.rindex(".") + 1 :]
        try:
            match fileType:
                case "zip":
                    self.handle_zip_file(self.file_input.value)
                case "csv":
                    self.handle_csv_file(file_content=self.file_input.value)
                case "bin":
                    self.handle_bin_file(
                        file_name=self.file_input.filename,
                        file_content=self.file_input.value,
                    )
                case "xlsx":
                    self.handle_xlsx_file(
                        file_content=self.file_input.value,
                        filename=self.file_input.filename,
                    )
                case _:
                    pn.state.notifications.error("No matching parser found")
                    self.ready = False
                    return
            if self.ready:
                pn.state.notifications.success(
                    "File uploaded successfully", duration=5000
                )
            else:
                pn.state.notifications.error("File upload failed", duration=5000)
        except Exception as e:
            self.ready = False
            pn.state.notifications.error(f"File upload failed: {str(e)}", duration=5000)

    def handle_zip_file(self, input_zip: bytes):
        datasets, subject_data_dict = self.extract_zip(input_zip)
        if datasets is None or subject_data_dict is None:
            self.ready = False
            return
        try:
            subject_synced = {}
            sampling_rates = []
            for subject in subject_data_dict.keys():
                fs, df = self.sync_session(datasets=subject_data_dict[subject])
                subject_synced[subject] = df
                sampling_rates.append(fs)
            self.data = subject_synced
            self.sampling_rate = sampling_rates[0]
            self.ready = True
        except Exception:
            subject_phase_data_dict = {}
            for subject in subject_data_dict.keys():
                dataset_list = [
                    bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
                    for dataset in subject_data_dict[subject]
                ]
                fs_list = [fs for df, fs in dataset_list]
                df_all = pd.concat([df for df, fs in dataset_list], axis=0)
                self.sampling_rate = fs_list[0]
                subject_phase_data_dict[subject] = df_all
            self.data = subject_phase_data_dict
            self.ready = True

    @staticmethod
    def sync_session(datasets: List[Dataset]) -> Tuple[float, pd.DataFrame]:
        for dataset in datasets:
            _handle_counter_inconsistencies_dataset(dataset, "ignore")
        synced = SyncedSession(datasets)
        synced.align_to_syncregion(inplace=True)
        df = synced.data_as_df(None, index="local_datetime", concat_df=True)
        df.index.name = "time"
        if len(set(synced.info.sampling_rate_hz)) > 1:
            raise ValueError()
        fs = synced.info.sampling_rate_hz[0]
        return fs, df

    def extract_zip(
        self, input_zip: bytes
    ) -> Tuple[List[Dataset], Dict[str, List[Dataset]]]:
        input_zip = ZipFile(BytesIO(input_zip))
        datasets = []
        subject_data_dict = {}
        for file in input_zip.infolist():
            if file.filename.startswith("__"):
                continue
            if ".bin" in file.filename:
                dataset, subject_id = self.read_zipped_bin_file(file, input_zip)
                datasets.append(dataset)
                if subject_id in subject_data_dict.keys():
                    subject_data_dict[subject_id].append(dataset)
                else:
                    subject_data_dict[subject_id] = [dataset]
        return datasets, subject_data_dict

    def read_zipped_bin_file(
        self, file: zipfile.ZipInfo, input_zip: ZipFile
    ) -> Tuple[Dataset, str]:
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=BytesIO(input_zip.read(file.filename)),
            legacy_support="resolve",
            tz=self.timezone,
        )
        subject_id = self.extract_subject_id(file.filename)
        return dataset, subject_id

    @staticmethod
    def extract_subject_id(filename: str) -> str:
        if "/" not in filename and "_" not in filename:
            Exception("The archive has the wrong structure")
        if "/" not in filename:
            return filename.split(".")[0].split("_")[-1]
        filenames = filename.split("/")
        if len(filenames) > 3 or len(filenames) < 2:
            Exception("The archive has the wrong structure")
        elif len(filenames) == 2 and "_" in filenames[1] and "." in filenames[1]:
            return filenames[1].split(".")[0].split("_")[-1]
        elif len(filenames) == 3:
            return filenames[1]
        else:
            Exception("The archive has the wrong structure")

    def handle_csv_file(self, file_name: string, file_content: bytes):
        string_io = StringIO(file_content.decode("utf8"))
        df = pd.read_csv(string_io)
        if self.selected_signal == "EEG":
            self.data = {file_name: MuseDataset(data=df, tz=self.timezone)}
        else:
            self.data = {file_name: self.convert_columns(df)}
        if self.data is None or len(self.data) == 0:
            Exception("No data found in file")
        self.ready = True

    @staticmethod
    def convert_columns(df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if "timestamp" in col.lower():
                try:
                    df[col] = pd.Timestamp(df[col])
                    df.set_index(col, inplace=True)
                except ValueError:
                    pass
            elif "time" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                    df.set_index(col, inplace=True)
                except ValueError:
                    pass
        return df

    def handle_bin_file(self, file_name: string, file_content: bytes):
        dataset = NilsPodAdapted.from_bin_file(
            filepath_or_buffer=BytesIO(file_content),
            legacy_support="resolve",
            tz=self.timezone,
        )
        self.sensors = set(dataset.info.enabled_sensors)
        df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
        self.sampling_rate = fs
        self.data = {file_name: df}
        self.ready = True

    def handle_xlsx_file(self, file_content: bytes, filename: string):
        if self.selected_signal == "CFT":
            dict_hr: HeartRatePhaseDict = pd.read_excel(
                BytesIO(file_content), index_col="time", sheet_name=None
            )
            dict_hr = {k: v.tz_localize(self.timezone) for k, v in dict_hr.items()}
            self.data = dict_hr
        if "hr_result" in filename:
            subject_id = re.findall("hr_result_(Vp\w+).xlsx", filename)[0]
            hr = pd.read_excel(BytesIO(file_content), sheet_name=None, index_col="time")
            self.hr_data[subject_id] = hr
        self.ready = True

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
        ("session", param.Dynamic),
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
            self.session,
            self.sensors,
            self.timezone,
        )

    def panel(self):
        self.ready = self.data is not None
        if self.recording == "Multiple Recording":
            self.file_input.accept = ".zip"
        else:
            self.file_input.accept = ".csv,.bin,.xlsx"
        return self._view

    #
    # def handle_single_session(self):
    #     for val, fn in zip(self.file_input.value, self.file_input.filename):
    #         self.handle_single_file(val, fn)
    #         if fn.endswith(".bin"):
    #             (
    #                 self.data,
    #                 self.sampling_rate,
    #             ) = biopsykit.io.nilspod.load_dataset_nilspod(dataset=self.data[0])
    #         self.ready = True

    # def handle_multi_not_synced_sessions(self):
    #     if self.data is dict:
    #         return
    #     session_names = [
    #         name.split(".")[0].split("_")[-1]
    #         for name in self.file_input.filename
    #         if "xls" not in name
    #     ]
    #     for val, fn in zip(self.file_input.value, self.file_input.filename):
    #         if "xls" in fn:
    #             continue
    #         self.handle_single_file(val, fn)
    #     dataset_dict = {
    #         vp: self.dataset_to_df(ds) for vp, ds in zip(session_names, self.data)
    #     }
    #     self.sampling_rate = [
    #         ds.info.sampling_rate_hz for vp, ds in zip(session_names, self.data)
    #     ]
    #     if self.sampling_rate.count(self.sampling_rate[0]) != len(self.sampling_rate):
    #         pn.state.notifications.error("One sampling rate is different!")
    #         return
    #     self.sampling_rate = self.sampling_rate[0]
    #     self.data = dataset_dict
    #     self.ready = True

    # def dataset_to_df(self, ds):
    #     df = ds.data_as_df()
    #     start = ds.info.utc_datetime_start
    #     sr = ds.info.sampling_rate_hz
    #     step = datetime.timedelta(seconds=1 / sr)
    #     my_ind = [start]
    #     for i in range(len(df) - 1):
    #         c = my_ind[i]
    #         x = my_ind[i] + step
    #         my_ind.append(x)
    #     a = pd.Index(my_ind)
    #     df.set_index(a, inplace=True)
    #     df.index.name = "index"
    #     return df

    # def handle_synced_sessions(self):
    #     for val, fn in zip(self.file_input.value, self.file_input.filename):
    #         self.handle_single_file(val, fn)
    #     session = SyncedSession(self.data)
    #     session.align_to_syncregion(inplace=True)
    #     _handle_counter_inconsistencies_dataset(session, "ignore")
    #     df = session.data_as_df(None, index="local_datetime", concat_df=True)
    #     df.index.name = "time"
    #     if len(set(session.info.sampling_rate_hz)) > 1:
    #         raise ValueError(
    #             f"Datasets in the sessions have different sampling rates! Got: {session.info.sampling_rate_hz}."
    #         )
    #     fs = session.info.sampling_rate_hz[0]
    #     self.data = df
    #     self.sampling_rate = fs
    #     self.ready = True

    # def handle_single_file(self, value, filename):
    #     if filename.endswith(".bin"):
    #         self.handle_bin_file(bytefile=BytesIO(value))
    #         pn.state.notifications.success(filename)
    #     elif filename.endswith(".csv"):
    #         self.handle_csv_file(bytefile=value)
    #     else:
    #         pn.state.notifications.error("Not a matching file format")

    # def extract_zip(self, input_zip: bytes):
    #     input_zip = ZipFile(BytesIO(input_zip))
    #     datasets = []
    #     path = zipfile.Path(input_zip)
    #     subject_data_dict = {}
    #     for file_path in path.iterdir():
    #         if file_path.name.startswith("__"):
    #             continue
    #         if file_path.is_dir():
    #             subject_id = file_path.name
    #             ds = []
    #             for file in file_path.iterdir():
    #                 if ".bin" in file.name:
    #                     dataset = NilsPodAdapted.from_bin_file(
    #                         filepath_or_buffer=BytesIO(input_zip.read(file.at)),
    #                         legacy_support="resolve",
    #                         tz=self.timezone,
    #                     )
    #                     ds.append(dataset)
    #             subject_data_dict[subject_id] = ds
    #         elif ".bin" in file_path.name:
    #             subject_id = file_path.name.split(".")[0].split("_")[-1]
    #             dataset = NilsPodAdapted.from_bin_file(
    #                 filepath_or_buffer=BytesIO(input_zip.read(file_path.name)),
    #                 legacy_support="resolve",
    #                 tz=self.timezone,
    #             )
    #             datasets.append(dataset)
    #             if subject_id in subject_data_dict.keys():
    #                 subject_data_dict[subject_id].append(dataset)
    #             else:
    #                 subject_data_dict[subject_id] = [dataset]
    #             # subject_data_dict[subject_id] = {}
    #     # for name in input_zip.namelist():
    #     #     if name.startswith("__"):
    #     #         continue
    #     #     subject_id = name.split(".")[0].split("_")[-1]
    #     #     if ".bin" in name:
    #     #         dataset = NilsPodAdapted.from_bin_file(
    #     #             filepath_or_buffer=BytesIO(input_zip.read(name)),
    #     #             legacy_support="resolve",
    #     #             tz=self.timezone,
    #     #         )
    #     #         datasets.append(dataset)
    #     try:
    #         subject_synced = {}
    #         for subject in subject_data_dict.keys():
    #             synced = SyncedSession(datasets)
    #             synced.align_to_syncregion(inplace=True)
    #             _handle_counter_inconsistencies_dataset(synced, "ignore")
    #             df = synced.data_as_df(None, index="local_datetime", concat_df=True)
    #             df.index.name = "time"
    #             if len(set(synced.info.sampling_rate_hz)) > 1:
    #                 raise ValueError(
    #                     f"Datasets in the sessions have different sampling rates! Got: {synced.info.sampling_rate_hz}."
    #                 )
    #             fs = synced.info.sampling_rate_hz[0]
    #             subject_synced[subject] = df
    #         self.data = subject_synced
    #         self.sampling_rate = fs
    #         self.ready = True
    #     except Exception:
    #         # pn.state.notifications.warning("Could not sync data")
    #         subject_phase_data_dict = {}
    #         for subject in subject_data_dict.keys():
    #             dataset_list = [
    #                 biopsykit.io.nilspod.load_dataset_nilspod(dataset=dataset)
    #                 for dataset in subject_data_dict[subject]
    #             ]
    #             fs_list = [fs for df, fs in dataset_list]
    #             df_all = pd.concat([df for df, fs in dataset_list], axis=0)
    #             self.sampling_rate = fs_list[0]
    #             # phase_names = [f"Part{i}" for i in range(len(dataset_list))]
    #             # dataset_dict = {
    #             #     phase: df for phase, (df, fs) in zip(phase_names, dataset_list)
    #             # }
    #             # subject_phase_data_dict[subject] = dataset_dict
    #             subject_phase_data_dict[subject] = df_all
    #         self.data = subject_phase_data_dict
    #         self.ready = True
