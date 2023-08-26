import param
import panel as pn
import biopsykit as bp
from biopsykit.protocols import CFT
from biopsykit.signals.ecg import EcgProcessor
from biopsykit.signals.eeg import EegProcessor
from nilspodlib import Dataset
import plotly.express as px
import matplotlib.pyplot as plt
from fau_colors import cmaps

from src.Physiological.CONSTANTS import PROCESSING_PREVIEW_TEXT, PRESTEP_PROCESSING_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class ProcessingPreStep(PhysiologicalBase):
    ready = param.Boolean(default=False)
    ready_btn = pn.widgets.Button(name="Ok", button_type="primary")

    def __init__(self, **params):
        params["HEADER_TEXT"] = PRESTEP_PROCESSING_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.ready_btn.link(self, callbacks={"clicks": self.ready_btn_click})
        pane = pn.Column(self.header)
        pane.append(self.ready_btn)
        self._view = pane

    def ready_btn_click(self, target, event):
        self.ready = True

    def panel(self):
        return self._view


class ProcessingAndPreview(PhysiologicalBase):
    phase_title = pn.widgets.StaticText(name="Phase", visible=False)
    results = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = PROCESSING_PREVIEW_TEXT
        super().__init__(**params)
        self.update_step(9)
        pane = pn.Column(self.header)
        pane.append(self.results)
        self._view = pane

    def get_phases(self) -> list:
        if self.subject is not None:
            return self.ecg_processor[self.subject].phases
        if type(self.ecg_processor) != dict:
            return self.ecg_processor.phases
        keys = list(self.ecg_processor.keys())
        if len(keys) == 1:
            return self.ecg_processor[keys[0]].phases
        elif len(keys) > 1:
            return keys
        return ["data"]

    def processing(self):
        col = pn.Column()
        if self.selected_signal == "ECG":
            col = self.process_ecg()
        elif self.selected_signal == "EEG":
            col = self.process_eeg()
        elif self.selected_signal == "CFT":
            col = self.process_cft()
        elif self.selected_signal == "RSP":
            self.process_rsp()
        if not self.skip_hrv:
            col.append(self.process_hrv())
        return col

    def get_dataframes_as_accordions(self):
        accordion = pn.Accordion()
        df = self.data
        if type(self.data) == Dataset:
            df = self.data.data_as_df()
        if type(self.data) == dict:
            df = {}
            for key in self.data.keys():
                df[key] = self.data[key]
        if self.data_processed:
            return accordion
        # self.process_ecg()
        # if "ecg" in self.sensors:
        #     if self.subj_time_dict:
        #         time_log = self.subj_time_dict
        #         if self.session.value == "Single Session":
        #             time_log = self.subj_time_dict[self.subject]
        #             for key in time_log.keys():
        #                 time_log[key] = time_log[key].apply(
        #                     lambda dt: dt.time() if isinstance(dt, datetime) else dt
        #                 )
        #             time_log = time_log[list(time_log.keys())[0]]
        #         self.ecg_processor = EcgProcessor(
        #             data=df,
        #             sampling_rate=self.sampling_rate,
        #             time_intervals=time_log,
        #         )
        #     else:
        #         self.ecg_processor = EcgProcessor(
        #             data=df, sampling_rate=self.sampling_rate
        #         )
        #     if self.skip_outlier_detection:
        #         self.ecg_processor.ecg_process(
        #             outlier_correction=None,
        #             outlier_params=None,
        #         )
        #     else:
        #         self.ecg_processor.ecg_process(
        #             outlier_correction=self.outlier_methods,
        #             outlier_params=self.outlier_params,
        #         )
        #     self.data_processed = True
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

    def process_rsp(self):
        return

    def process_cft(self):
        cft = CFT()
        col = pn.Column()
        for sheet in self.cft_sheets:
            df_hr = self.data[sheet]
            df_cft = cft.extract_cft_interval(self.data[sheet])
            self.cft_processor[sheet] = {
                "Baseline": cft.baseline_hr(df_hr),
                "CFT": df_cft,
                "CFT Parameters": cft.compute_cft_parameter(df_hr),
                "HR": df_hr,
            }
            hr_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
            fig, _ = bp.signals.ecg.plotting.hr_plot(df_hr)
            hr_plot.object = fig
            cft_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
            fig, _ = cft.cft_plot(data=df_hr)
            cft_plot.object = fig
            col.append("## " + sheet)
            col.append(pn.layout.Divider())
            col.append(hr_plot)
            col.append(cft_plot)
        return col

    def get_timelog(self, subject: str):
        time_log = self.subject_time_dict
        if not bool(time_log):
            return None
        if self.session == "Single Session":
            time_log = self.subject_time_dict[subject]
            for key in time_log.keys():
                time_log[key] = time_log[key].apply(lambda dt: dt.time())
            time_log = time_log[list(time_log.keys())[0]]
        return time_log

    def process_eeg(self):
        col = pn.Column()
        if self.selected_signal == "EEG":
            if self.subject_time_dict:
                for subject in self.subject_time_dict.keys():
                    self.eeg_processor[subject] = EegProcessor(
                        data=self.data[subject],
                        sampling_rate=float(self.sampling_rate),
                        time_intervals=self.subject_time_dict[subject],
                    )
                    self.eeg_processor[subject].relative_band_energy(
                        freq_bands=self.freq_bands
                    )
            else:
                if self.sampling_rate != -1:
                    self.eeg_processor["Data"] = EegProcessor(
                        data=self.data, sampling_rate=float(self.sampling_rate)
                    )
                else:
                    self.eeg_processor["Data"] = EegProcessor(
                        data=self.data.data_as_df(index="local_datetime"),
                        sampling_rate=float(256),
                    )
                self.eeg_processor["Data"].relative_band_energy()
                fig = px.line(
                    self.eeg_processor["Data"].eeg_result["Data"],
                    color_discrete_sequence=cmaps.faculties,
                )
                fig.layout.autosize = True
                responsive = pn.pane.Plotly(fig, config={"responsive": True})
                col.append(responsive)
            self.data_processed = True
        return col

    def process_ecg(self):
        col = pn.Column()
        if not self.selected_signal == "ECG":
            pn.state.notifications.error("False Signal Selection")
            return col
        if type(self.data) != dict:
            if self.subject_time_dict:
                # One Subject mult. phases
                self.ecg_processor = EcgProcessor(
                    data=self.data, sampling_rate=self.sampling_rate
                )
            else:
                # One Subject one phase
                self.ecg_processor = EcgProcessor(
                    data=self.data,
                    sampling_rate=self.sampling_rate,
                    time_intervals=self.get_timelog(),
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
        elif self.session == "Single Session":
            # Multiple Phases single. subject
            self.ecg_processor = {}
            for subject in self.data.keys():
                ep = EcgProcessor(
                    data=self.data[subject], sampling_rate=self.sampling_rate
                )
                ep.ecg_process(
                    outlier_correction=self.selected_outlier_methods,
                    outlier_params=self.outlier_params,
                )
                self.ecg_processor[subject] = ep
                # pn.state.notifications.error("Error in ECG Processing: " + str(e))
        elif self.session == "Multiple Sessions":
            # Multiple Subjects mult. phases
            self.ecg_processor = {}
            for subject in self.data.keys():
                ep = EcgProcessor(
                    data=self.data[subject],
                    sampling_rate=self.sampling_rate,
                    time_intervals=self.get_timelog()[subject],
                )
                ep.ecg_process(title=subject)
                self.ecg_processor[subject] = ep
        accordion = self.get_dataframes_as_accordions()
        stat_values = self.get_statistical_values()
        for stat_value in stat_values:
            accordion.append(stat_value)
        col.append(accordion)
        select_phase = pn.widgets.Select(name="Select Phase", options=self.get_phases())
        ecg_plot = pn.pane.Matplotlib(plt.Figure(figsize=(15, 10)), tight=True)
        if self.subject is not None:
            fig, _ = bp.signals.ecg.plotting.ecg_plot(
                self.ecg_processor[self.subject], key=self.get_phases()[0]
            )
            ecg_plot.object = fig
            select_phase.link(ecg_plot, callbacks={"value": self.phase_changed})
            col.append(select_phase)
            self.phase_title.visible = True
            self.phase_title.value = self.get_phases()[0]
            col.append(self.phase_title)
            col.append(ecg_plot)
        self.data_processed = True
        return col

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
        # TODO: Condition List bekommen wir im TimeLog
        # dict_merged_cond = bp.utils.data_processing.split_subject_conditions(dict_merged, condition_list)

    def get_statistical_values(self):
        values = []
        if type(self.ecg_processor) != dict:
            for column in self.ecg_processor.ecg_result:
                if not "Rate" in column:
                    continue
                df = self.ecg_processor.ecg_result[column]
                fig = px.box(df, y=column)
                plotly_pane = pn.pane.Plotly(fig)
                values.append(("Boxplot  : " + column, plotly_pane))
        else:
            for subject in self.ecg_processor.keys():
                for column in self.ecg_processor[subject].ecg_result:
                    if not "Rate" in column:
                        continue
                    df = self.ecg_processor[subject].ecg_result[column]
                    fig = px.box(df, y=column)
                    plotly_pane = pn.pane.Plotly(fig)
                    values.append(("Boxplot " + subject + ": " + column, plotly_pane))
        return values

    def phase_changed(self, target, event):
        if self.subject is not None:
            fig, axs = bp.signals.ecg.plotting.ecg_plot(
                self.ecg_processor[self.subject], key=event.new
            )
            target.object = fig
            self.phase_title.value = event.new

    def process_hrv(self):
        if self.skip_hrv:
            return
        for key in self.ecg_processor.ecg_result.keys():
            for vp in self.subject_time_dict.keys():
                self.ecg_processor.hrv_process(
                    self.ecg_processor,
                    key,
                    index=vp,
                    hrv_types=self.hrv_types.value,
                    correct_rpeaks=self.correct_rpeaks.value,
                )
        # for vp in self.subj_time_dict.keys():
        #     self.dict_hr_subjects[vp] = self.ecg_processor.heart_rate

    def panel(self):
        self.results = self.processing()
        return self._view
