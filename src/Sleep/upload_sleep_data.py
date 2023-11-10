from io import BytesIO, StringIO
from zipfile import ZipFile

import biopsykit as bp
import pandas as pd
import panel as pn
import param

from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.Sleep.SLEEP_CONSTANTS import UPLOAD_SLEEP_DATA_TEXT
from src.Sleep.sleep_base import SleepBase
from src.utils import load_withings_sleep_analyzer_raw_file


class UploadSleepData(SleepBase):
    fs = param.Dynamic(default=None)
    ready = param.Boolean(default=False)
    accepted_file_types = {
        "Polysomnography": ".edf, .zip",
        "Other IMU Device": ".bin, .zip",
        "Withings": ".csv, .zip",
    }
    upload_data = pn.widgets.FileInput(
        name="Upload sleep data",
        multiple=False,
        sizing_mode="stretch_width",
    )
    filename = param.String(default="")

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_SLEEP_DATA_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(UPLOAD_SLEEP_DATA_TEXT)
        self.upload_data.link(
            self,
            callbacks={
                "filename": self.filename_changed,
            },
        )
        self._view = pn.Column(self.header, self.upload_data)

    def filename_changed(self, _, event):
        self.filename = event.new
        if self.filename is None or self.filename == "" or "." not in self.filename:
            return
        pn.state.notifications.info("Processing data...")
        self.process_data()

    def process_data(self):
        try:
            if self.upload_data.value is None:
                self.ready = False
                pn.state.notifications.error("Please upload a file")
            elif self.selected_device == "Polysomnography":
                self.parse_psg()
            elif self.selected_device == "Other IMU Device":
                self.parse_other_imu()
            elif self.selected_device == "Withings":
                self.parse_withings()
            else:
                pn.state.notifications.error("Please choose a device")
                self.ready = False
                return
            self.ready = True
        except Exception as e:
            print(f"Exception in upload_sleep_data: {e}")
            self.ready = False

    def parse_psg(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        elif self.upload_data.filename.endswith(".edf"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
        else:
            pn.state.notifications.error("Please upload a zip or edf file")
            self.ready = False

    def parse_other_imu(self):
        pn.state.notifications.info("Parsing imu data...")
        if self.upload_data.filename.endswith(".bin"):
            dataset = NilsPodAdapted.from_bin_file(
                filepath_or_buffer=BytesIO(self.upload_data.value),
                legacy_support="resolve",
                **self.selected_parameters[self.selected_device],
            )
            df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
            self.add_data(df, self.upload_data.filename)
            self.sampling_rate = fs
        elif self.upload_data.filename.endswith(".csv"):
            string_io = StringIO(self.upload_data.value.decode("utf-8"))
            dataset = pd.read_csv(string_io)
            self.add_data(dataset, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".zip"):
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".bin"):
                    dataset = NilsPodAdapted.from_bin_file(
                        filepath_or_buffer=BytesIO(input_zip.read(file)),
                        **self.selected_parameters[self.selected_device],
                    )
                    datasets.append(dataset)
                elif file.filename.endswith(".csv"):
                    string_io = StringIO(str(input_zip.open(file)))
                    dataset = pd.read_csv(string_io)
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        self.ready = True

        pn.state.notifications.success("Successfully loaded data")

    def parse_withings(self):
        if self.upload_data.filename.endswith(".zip"):
            pn.state.notifications.error("Not yet implemented")
            self.ready = False
            input_zip = ZipFile(BytesIO(self.upload_data.value))
            datasets = []
            list_of_files = input_zip.infolist()
            for file in list_of_files:
                if file.filename.endswith(".csv"):
                    dataset = self.load_withings(
                        file=bytes(input_zip.read(file)),
                        filename=file.filename,
                    )
                    datasets.append(dataset)
            self.add_data(datasets, self.upload_data.filename)
        elif self.upload_data.filename.endswith(".csv"):
            dataset = self.load_withings(
                file=bytes(self.upload_data.value), filename=self.upload_data.filename
            )
            self.add_data(dataset, self.upload_data.filename)
        self.ready = True
        pn.state.notifications.success("Successfully loaded data")

    def load_withings(self, file: bytes, filename):
        dataset = load_withings_sleep_analyzer_raw_file(
            file=file,
            file_name=filename,
            **self.selected_parameters[self.selected_device]
            # data_source=self.selected_parameters["data_source"],
            # timezone=self.selected_parameters["timezone"],
            # split_into_nights=self.selected_parameters["split_into_nights"],
        )
        return dataset

    def panel(self):
        # if self.selected_device == "Other IMU Device":
        #     self.next_page = "Convert Acc to g"
        self.upload_data.accept = self.accepted_file_types[self.selected_device]
        # self.upload_data.link(
        #     self,
        #     callbacks={
        #         "value": self.filename_changed,
        #     },
        # )
        return self._view
