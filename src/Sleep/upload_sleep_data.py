from io import BytesIO, StringIO
from zipfile import ZipFile

import biopsykit as bp
import pandas as pd
import panel as pn
import param

from src.Physiological.AdaptedNilspod import NilsPodAdapted
from src.utils import load_withings_sleep_analyzer_raw_file


class UploadSleepData(param.Parameterized):
    selected_device = param.String(default="")
    data = param.Dynamic(default=None)
    fs = param.Dynamic(default=None)
    ready = param.Boolean(default=False)
    accepted_file_types = {
        "Polysomnography": [".edf, .zip"],
        "Other IMU Device": [".bin, .zip"],
        "Withings": [".csv, .zip"],
    }
    upload_data = pn.widgets.FileInput(
        name="Upload sleep data",
        multiple=False,
    )
    selected_parameters = param.Dict(default={})
    next_page = param.Selector(
        default="Process Data",
        objects=["Process Data", "Convert Acc to g"],
    )

    def process_data(self, _):
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
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
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
        try:
            if self.upload_data.filename.endswith(".bin"):
                dataset = NilsPodAdapted.from_bin_file(
                    filepath_or_buffer=BytesIO(self.upload_data.value),
                    **self.selected_parameters,
                )
                df, _ = bp.io.nilspod.load_dataset_nilspod(dataset=dataset)
                self.data = [df]
            elif self.upload_data.filename.endswith(".csv"):
                string_io = StringIO(self.upload_data.value.decode("utf-8"))
                dataset = pd.read_csv(string_io)
                self.data = [dataset]
            elif self.upload_data.filename.endswith(".zip"):
                input_zip = ZipFile(BytesIO(self.upload_data.value))
                datasets = []
                list_of_files = input_zip.infolist()
                for file in list_of_files:
                    if file.filename.endswith(".bin"):
                        dataset = NilsPodAdapted.from_bin_file(
                            filepath_or_buffer=input_zip.open(file),
                            **self.selected_parameters,
                        )
                        datasets.append(dataset)
                    elif file.filename.endswith(".csv"):
                        string_io = StringIO(input_zip.open(file))
                        dataset = pd.read_csv(string_io)
                        datasets.append(dataset)
                self.data = datasets
            self.ready = True
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

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
                        file=BytesIO(input_zip.open(file)),
                        filename=file.filename,
                    )
                    datasets.append(dataset)
            self.data = datasets
        elif self.upload_data.filename.endswith(".csv"):
            dataset = self.load_withings(
                file=BytesIO(self.upload_data.value), filename=self.upload_data.filename
            )
            self.data = [dataset]

    def load_withings(self, file, filename):
        dataset = load_withings_sleep_analyzer_raw_file(
            file=file,
            data_source=self.selected_parameters["data_source"],
            file_name=filename,
            timezone=self.selected_parameters["timezone"],
            split_into_nights=self.selected_parameters["split_into_nights"],
        )
        return dataset

    @param.output("selected_device", param.String, "data", param.Dynamic)
    def output(self):
        return (
            self.selected_device,
            self.data,
        )

    def panel(self):
        if self.selected_device == "Other IMU Device":
            self.next_page = "Convert Acc to g"
        text = "# Upload your sleep data \n Please upload your sleep data in the following step. You can either upload a single file or a zip file containing all your files."
        self.upload_data.accept = self.accepted_file_types[self.selected_device]
        self.upload_data.param.watch(self.process_data, "value")
        return pn.Column(pn.pane.Markdown(text), self.upload_data)
