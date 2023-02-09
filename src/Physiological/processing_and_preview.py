from datetime import datetime

import pandas as pd
import param
import panel as pn
import biopsykit as bp
from biopsykit.signals.ecg import EcgProcessor
from biopsykit.signals.eeg import EegProcessor
from nilspodlib import Dataset
import plotly.express as px
from matplotlib.figure import Figure
from matplotlib import cm
from src.Physiological.outlier_detection import AskToDetectOutliers
import matplotlib.pyplot as plt

from src.Physiological.process_hrv import AskToProcessHRV


class ProcessingPreStep(AskToProcessHRV):

    ready = param.Boolean(default=False)
    ready_btn = pn.widgets.Button(name="Ok", button_type="primary")

    def get_phases(self):
        keys = []
        if type(self.data) is dict:
            keys = self.data.keys()
        elif self.ecg_processor.phases:
            keys = self.ecg_processor.phases
        else:
            keys = ["data"]
        return keys

    def ready_btn_click(self, event):
        self.ready = True

    def panel(self):
        self.step = 8
        self.set_progress_value()
        self.ready_btn.on_click(self.ready_btn_click)
        if self.text == "":
            f = open("../assets/Markdown/ProcessingPreSteps.md", "r")
            fileString = f.read()
            self.text = fileString
        column = pn.Column(pn.Row(self.get_step_static_text()))
        column.append(self.progress)
        column.append(self.text)
        return column


class ProcessingAndPreview(ProcessingPreStep):
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
    phase_title = pn.widgets.StaticText(name="Phase", visible=False)

    def get_dataframes_as_accordions(self):
        accordion = pn.Accordion()
        df = self.data
        if type(self.data) == Dataset:
            df = self.data.data_as_df()
        if type(self.data) == dict:
            df = {}
            for key in self.data.keys():
                df[key] = self.data[key]
        if self.ecg_processed:
            return accordion
        if "ecg" in self.sensors:
            if self.subj_time_dict:
                time_log = self.subj_time_dict
                if self.session.value == "Single Session":
                    time_log = self.subj_time_dict[self.subject]
                    for key in time_log.keys():
                        time_log[key] = time_log[key].apply(
                            lambda dt: dt.time() if isinstance(dt, datetime) else dt
                        )
                    time_log = time_log[list(time_log.keys())[0]]
                self.ecg_processor = EcgProcessor(
                    data=df,
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_log,
                )
            else:
                self.ecg_processor = EcgProcessor(
                    data=df, sampling_rate=self.sampling_rate
                )
            if self.skip_outlier_detection:
                self.ecg_processor.ecg_process(
                    outlier_correction=None,
                    outlier_params=None,
                )
            else:
                self.ecg_processor.ecg_process(
                    outlier_correction=self.outlier_methods,
                    outlier_params=self.outlier_params,
                )
            self.ecg_processed = True
            # if type(self.data) == dict:
            #     for key in self.data.keys():
            #         ecg_results = pn.widgets.DataFrame(
            #             name=key + " ECG Results",
            #             value=self.ecg_processor.ecg_result[key],
            #         )
            #         hr_results = pn.widgets.DataFrame(
            #             name=key + " HR Results",
            #             value=self.ecg_processor.hr_result[key],
            #         )
            #         rsp_signal = self.ecg_processor.ecg_estimate_rsp(
            #             self.ecg_processor, key=key, edr_type="peak_trough_diff"
            #         )
            #         rsa = self.ecg_processor.rsa_process(
            #             ecg_signal=self.ecg_processor.ecg_result[key],
            #             rsp_signal=rsp_signal,
            #             sampling_rate=self.sampling_rate,
            #         )
            #         accordion.append(ecg_results)
            #         accordion.append(hr_results)
            # else:
            #     ecg_results = pn.widgets.DataFrame(
            #         name="ECG Results",
            #         value=self.ecg_processor.ecg_result[self.get_phases()[0]],
            #     )
            #     hr_results = pn.widgets.DataFrame(
            #         name="HR Results",
            #         value=self.ecg_processor.hr_result[self.get_phases()[0]],
            #     )
            # rsp_signal = self.ecg_processor.ecg_estimate_rsp(
            #     self.ecg_processor, key="Data", edr_type="peak_trough_diff"
            # )
            # rsa = self.ecg_processor.rsa_process(
            #     ecg_signal=self.ecg_processor.ecg_result[
            #         self.ecg_processor.ecg_result.keys()[0]
            #     ],
            #     rsp_signal=rsp_signal,
            #     sampling_rate=self.sampling_rate,
            # )
        #         accordion.append(ecg_results)
        #         accordion.append(hr_results)
        # if "eeg" in self.sensors:
        #     self.eeg_processor = EegProcessor(df, self.sampling_rate)
        #     self.eeg_processor.relative_band_energy()
        #     if type(self.data) == dict:
        #         for key in self.data.keys():
        #             df_bands = pn.widgets.DataFrame(
        #                 name=key + " Frequency Bands",
        #                 value=self.eeg_processor.eeg_result[key],
        #             )
        #             accordion.append(df_bands)
        #     else:
        #         df_bands = pn.widgets.DataFrame(
        #             name="Frequency Bands",
        #             value=self.eeg_processor.eeg_result[
        #                 self.eeg_processor.eeg_result.keys()[0]
        #             ],
        #         )
        #         accordion.append(df_bands)
        return accordion

    def process_ecg(self):
        if "ecg" in self.sensors:
            if self.subj_time_dict:
                time_log = self.subj_time_dict
                if self.session.value == "Single Session":
                    time_log = self.subj_time_dict[self.subject]
                    for key in time_log.keys():
                        time_log[key] = time_log[key].apply(lambda dt: dt.time())
                    time_log = time_log[list(time_log.keys())[0]]
                self.ecg_processor = EcgProcessor(
                    data=self.data,
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_log,
                )
            else:
                self.ecg_processor = EcgProcessor(
                    data=self.data, sampling_rate=self.sampling_rate
                )
            if self.skip_outlier_detection:
                self.ecg_processor.ecg_process(
                    outlier_correction=None,
                    outlier_params=None,
                )
            else:
                self.ecg_processor.ecg_process(
                    outlier_correction=self.outlier_methods,
                    outlier_params=self.outlier_params,
                )

    # TODO: noch den Baseline abfragen, und abfragen welche Phasen gewählt werden sollen
    def process_hr(self):
        if self.hr_data is None:
            return
        dict_result = bp.utils.data_processing.resample_dict_sec(self.hr_data)
        dict_result_norm = bp.utils.data_processing.normalize_to_phase(
            dict_result, "Baseline"
        )
        dict_result_norm_selected = bp.utils.data_processing.select_dict_phases(
            dict_result_norm, phases=["Intervention", "Stress", "Recovery"]
        )
        dict_study = bp.utils.data_processing.rearrange_subject_data_dict(
            dict_result_norm
        )
        dict_result = bp.utils.data_processing.cut_phases_to_shortest(dict_study)
        dict_merged = bp.utils.data_processing.merge_study_data_dict(dict_result)
        # TODO: Condotion List bekommen wir im TimeLog
        # dict_merged_cond = bp.utils.data_processing.split_subject_conditions(dict_merged, condition_list)

    def get_statistical_values(self):
        values = []
        for key in self.get_phases():
            for column in self.ecg_processor.ecg_result[key]:
                if not "Rate" in column:
                    continue
                df = self.ecg_processor.ecg_result[key]
                fig = px.box(df, y=column)
                plotly_pane = pn.pane.Plotly(fig)
                values.append(("Boxplot " + key + ": " + column, plotly_pane))
        return values

    def phase_changed(self, target, event):
        fig, axs = bp.signals.ecg.plotting.ecg_plot(self.ecg_processor, key=event.new)
        target.object = fig
        self.phase_title.value = event.new

    def process_hrv(self):
        if self.skip_hrv:
            return
        for key in self.ecg_processor.ecg_result.keys():
            for vp in self.subj_time_dict.keys():
                self.ecg_processor.hrv_process(
                    self.ecg_processor,
                    key,
                    index=vp,
                    hrv_types=self.hrv_types.value,
                    correct_rpeaks=self.correct_rpeaks.value,
                )
        pn.state.notifications.success("HRV processed successfully")
        # for vp in self.subj_time_dict.keys():
        #     self.dict_hr_subjects[vp] = self.ecg_processor.heart_rate

    def panel(self):
        if self.textHeader == "":
            f = open("../assets/Markdown/ProcessingAndPreview.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        column = pn.Column(self.textHeader)
        accordion = self.get_dataframes_as_accordions()
        self.process_hrv()
        stat_values = self.get_statistical_values()
        for stat_value in stat_values:
            accordion.append(stat_value)
        column.append(accordion)
        select_phase = pn.widgets.Select(name="Select Phase", options=self.get_phases())
        ecg_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
        fig, _ = bp.signals.ecg.plotting.ecg_plot(
            self.ecg_processor, key=self.get_phases()[0]
        )
        ecg_plot.object = fig
        select_phase.link(ecg_plot, callbacks={"value": self.phase_changed})
        column.append(select_phase)
        self.phase_title.visible = True
        self.phase_title.value = self.get_phases()[0]
        column.append(self.phase_title)
        column.append(ecg_plot)
        return column
