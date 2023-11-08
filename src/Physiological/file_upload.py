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
from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Physiological.PHYSIOLOGICAL_CONSTANTS import FILE_UPLOAD_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.utils import get_datetime_columns_of_data_frame
from io import BytesIO
from io import StringIO
from nilspodlib import SyncedSession, Dataset
from src.utils import _handle_counter_inconsistencies_dataset


class FileUpload(PhysiologicalBase):
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xlsx",
        sizing_mode="stretch_width",
    )
    select_timezone = pn.widgets.Select(
        options=["None Selected"] + list(pytz.all_timezones),
        value="Europe/Berlin",
        name="Timezone",
        sizing_mode="stretch_width",
    )
    select_hardware = pn.widgets.Select(
        options=["NilsPod", "BioPac"],
        value="NilsPod",
        name="Hardware",
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)
    filename = param.String(default=None)

    def __init__(self, **params):
        params["HEADER_TEXT"] = FILE_UPLOAD_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.select_timezone.link(self, callbacks={"value": self.timezone_changed})
        self.select_hardware.link(self, callbacks={"value": self.hardware_changed})
        self._select_hardware = pn.widgets.Select.from_param(self.param.hardware)
        self.file_input.link(
            self,
            callbacks={
                "filename": self.filename_changed,
            },
        )
        self._view = pn.Column(
            self.header,
            self.select_hardware,
            self.select_timezone,
            self.file_input,
        )

    def filename_changed(self, _, event):
        self.filename = event.new
        print(self.filename)
        if self.filename is None or "." not in self.filename:
            return
        if self.file_input.value is not None:
            self.parse_file_input(self.file_input, self.file_input.value)

    def timezone_changed(self, _, event):
        self.timezone = event.new
        if self.timezone == "None Selected":
            self.ready = False
        else:
            self.ready = True

    def hardware_changed(self, _, event):
        self.hardware = event.new
        if self.hardware == "NilsPod":
            self.file_input.accept = ".csv,.bin, .zip"
        if self.hardware == "BioPac":
            self.file_input.accept = ".acq"

    def parse_file_input(self, _, event):
        self.ready = self.data is not None
        self.data = None
        if self.file_input.value is None or len(self.file_input.value) <= 0:
            pn.state.notifications.error("No file uploaded")
            return
        print("parse file input 1")
        print(self.filename)
        if self.filename is None or "." not in self.filename:
            print("no filename found")
            return
        print("parse file input 2")
        fileType = self.file_input.filename[self.file_input.filename.rindex(".") + 1 :]
        print(f"{fileType}")
        try:
            match fileType:
                case "zip":
                    self.handle_zip_file(self.file_input.value)
                case "csv":
                    self.handle_csv_file(
                        file_name=self.filename,
                        file_content=self.file_input.value,
                    )
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
            # if self.ready:
            #     pn.state.notifications.success(
            #         "File uploaded successfully", duration=5000
            #     )
            # else:
            #     pn.state.notifications.error("File upload failed", duration=5000)
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
        print("handle csv file")
        string_io = StringIO(file_content.decode("utf8"))
        if string_io is None:
            print("no string found")
        df = pd.read_csv(string_io)
        if df is None:
            print("no data found")
        if self.signal == "EEG":
            muse = MuseDataset(data=df, tz=self.timezone)
            df = muse.data_as_df("local_datetime")
            self.sampling_rate = muse.sampling_rate_hz
            self.data = {file_name: df}
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
            tz=self.timezone,
        )
        self.sensors = set(dataset.info.enabled_sensors)
        df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
        self.sampling_rate = fs
        self.data = {file_name: df}
        self.ready = True
        pn.state.notifications.success("File uploaded successfully")

    def handle_xlsx_file(self, file_content: bytes, filename: string):
        if self.signal == "CFT":
            dict_hr = pd.read_excel(
                BytesIO(file_content), index_col="time", sheet_name=None
            )
            dict_hr = {k: v.tz_localize(self.timezone) for k, v in dict_hr.items()}
            self.data[filename] = dict_hr
        if "hr_result" in filename:
            subject_id = re.findall("hr_result_(Vp\w+).xlsx", filename)[0]
            hr = pd.read_excel(BytesIO(file_content), sheet_name=None, index_col="time")
            self.hr_data[subject_id] = hr
        self.ready = True

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone)

    def panel(self):
        self.ready = self.data is not None
        if self.recording == "Multiple Recording":
            self.file_input.accept = ".zip"
        else:
            self.file_input.accept = ".csv,.bin,.xlsx"
        return self._view
