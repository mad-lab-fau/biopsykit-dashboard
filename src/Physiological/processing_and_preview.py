import pandas as pd
import param
import panel as pn
from biopsykit.signals.ecg import EcgProcessor
from biopsykit.signals.eeg import EegProcessor
from nilspodlib import Dataset
import plotly.express as px

from src.Physiological.outlier_detection import AskToDetectOutliers


class ProcessingPreStep(AskToDetectOutliers):

    ready = param.Boolean(default=False)
    ready_btn = pn.widgets.Button(name="Ok", button_type="primary")

    def ready_btn_click(self, event):
        self.ready = True

    def panel(self):
        self.ready_btn.on_click(self.ready_btn_click)
        if self.text == "":
            f = open("../assets/Markdown/ProcessingPreSteps.md", "r")
            fileString = f.read()
            self.text = fileString
        column = pn.Column(self.text)
        return column


class ProcessingAndPreview(param.Parameterized):
    ecg_processor = param.Dynamic()
    eeg_processor = param.Dynamic()
    textHeader = ""
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    outlier_params = param.Dynamic()
    outlier_methods = param.Dynamic()
    sensors = param.Dynamic()
    time_log_present = param.Boolean()
    time_log = param.Dynamic()

    def panel(self):
        if self.textHeader == "":
            f = open("../assets/Markdown/ProcessingAndPreview.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        column = pn.Column(self.textHeader)
        accordion = self.get_dataframes_as_accordions()
        stat_values = self.get_statistical_values()
        for stat_value in stat_values:
            accordion.append(stat_value)
        column.append(accordion)
        return column

    def get_dataframes_as_accordions(self):
        accordion = pn.Accordion()
        df = self.data
        if type(self.data) == Dataset:
            df = self.data.data_as_df()
        if type(self.data) == dict:
            df = {}
            for key in self.data.keys():
                df[key] = self.data[key]

        if "ecg" in self.sensors:
            if self.time_log_present:
                self.ecg_processor = EcgProcessor(
                    data=df,
                    sampling_rate=self.sampling_rate,
                    time_intervals=self.time_log,
                )
            else:
                self.ecg_processor = EcgProcessor(
                    data=df, sampling_rate=self.sampling_rate
                )
            self.ecg_processor.ecg_process(
                outlier_correction=self.outlier_methods,
                outlier_params=self.outlier_params,
            )
            if type(self.data) == dict:
                for key in self.data.keys():
                    ecg_results = pn.widgets.DataFrame(
                        name=key + " ECG Results",
                        value=self.ecg_processor.ecg_result[key],
                    )
                    hr_results = pn.widgets.DataFrame(
                        name=key + " HR Results",
                        value=self.ecg_processor.hr_result[key],
                    )
                    rsp_signal = self.ecg_processor.ecg_estimate_rsp(
                        self.ecg_processor, key=key, edr_type="peak_trough_diff"
                    )
                    rsa = self.ecg_processor.rsa_process(
                        ecg_signal=self.ecg_processor.ecg_result[key],
                        rsp_signal=rsp_signal,
                        sampling_rate=self.sampling_rate,
                    )
                    accordion.append(ecg_results)
                    accordion.append(hr_results)
            else:
                ecg_results = pn.widgets.DataFrame(
                    name="ECG Results", value=self.ecg_processor.ecg_result["Data"]
                )
                hr_results = pn.widgets.DataFrame(
                    name="HR Results", value=self.ecg_processor.hr_result["Data"]
                )
                rsp_signal = self.ecg_processor.ecg_estimate_rsp(
                    self.ecg_processor, key="Data", edr_type="peak_trough_diff"
                )
                rsa = self.ecg_processor.rsa_process(
                    ecg_signal=self.ecg_processor.ecg_result["Data"],
                    rsp_signal=rsp_signal,
                    sampling_rate=self.sampling_rate,
                )
                accordion.append(ecg_results)
                accordion.append(hr_results)
        if "eeg" in self.sensors:
            self.eeg_processor = EegProcessor(df, self.sampling_rate)
            self.eeg_processor.relative_band_energy()
            if type(self.data) == dict:
                for key in self.data.keys():
                    df_bands = pn.widgets.DataFrame(
                        name=key + " Frequency Bands",
                        value=self.eeg_processor.eeg_result[key],
                    )
                    accordion.append(df_bands)
            else:
                df_bands = pn.widgets.DataFrame(
                    name="Frequency Bands", value=self.eeg_processor.eeg_result["Data"]
                )
                accordion.append(df_bands)
        return accordion

    def get_statistical_values(self):
        keys = []
        values = []
        if type(self.data) is dict:
            keys = self.data.keys()
        else:
            keys = ["Data"]

        for key in keys:
            ecg_stats = self.ecg_processor.ecg_result[key].agg(
                {
                    "ECG_Raw": ["min", "max", "min", "median"],
                    "ECG_Clean": ["min", "max", "min", "median"],
                    "ECG_Quality": ["min", "max", "min", "median"],
                    "Heart_Rate": ["min", "max", "min", "median"],
                }
            )
            values.append(
                pn.widgets.DataFrame(
                    name=key + " ECG Statistical Values", value=ecg_stats
                )
            )
            for column in self.ecg_processor.ecg_result[key]:
                df = self.ecg_processor.ecg_result[key]
                fig = px.box(df, y=column)
                plotly_pane = pn.pane.Plotly(fig)
                values.append(("Boxplot " + key + ": " + column, plotly_pane))

            heart_rate_stats = self.ecg_processor.heart_rate[key].agg(
                {
                    "Heart_Rate": ["min", "max", "min", "median"],
                }
            )
            values.append(
                pn.widgets.DataFrame(
                    name=key + " Heart Rate Statistical Values", value=heart_rate_stats
                )
            )
        return values

    @param.output(
        ("data", param.Dynamic),
        ("sensors", param.Dynamic),
        ("ecg_processor", param.Dynamic),
        ("eeg_processor", param.Dynamic),
        ("time_log_present", param.Boolean),
        ("time_log", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.sensors,
            self.ecg_processor,
            self.eeg_processor,
            self.time_log_present,
            self.time_log,
        )
