import param
import panel as pn
import biopsykit as bp
from biopsykit.protocols import CFT
from biopsykit.signals.ecg import EcgProcessor
from biopsykit.signals.eeg import EegProcessor
from biopsykit.signals.rsp import RspProcessor
from nilspodlib import Dataset
import plotly.express as px
import matplotlib.pyplot as plt

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import (
    PROCESSING_PREVIEW_TEXT,
    PRESTEP_PROCESSING_TEXT,
)
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.custom_components import SubjectDataFrameView, PlotViewer


class ProcessingPreStep(PhysiologicalBase):
    ready = param.Boolean(default=False)
    ready_btn = pn.widgets.Button(name="Ok", button_type="primary")

    def __init__(self, **params):
        params["HEADER_TEXT"] = PRESTEP_PROCESSING_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.ready_btn.link(self, callbacks={"clicks": self.ready_btn_click})
        self._view = pn.Column(self.header, self.ready_btn)

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
        self.subject_time_dict = {}
        self.result_view = SubjectDataFrameView({})
        self.result_graph = PlotViewer(None, None, None)
        self._view = pn.Column(
            self.header, self.results, self.result_view, self.result_graph
        )

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
        if self.signal == "ECG":
            col = self.process_ecg()
        elif self.signal == "EEG":
            col = self.process_eeg()
        elif self.signal == "RSP":
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
        return accordion

    def process_rsp(self):
        if self.sampling_rate == -1:
            pn.state.notifications.error("Bitte eine sampling Rate eingeben")
            return
        if self.estimate_rsp:
            self.rsp_processor = {}
            for subject in self.data.keys():
                time_intervals = self.get_timelog(subject)
                ep = EcgProcessor(
                    data=self.data[subject],
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_intervals,
                )
                ep.ecg_process(
                    outlier_correction=self.selected_outlier_methods,
                    outlier_params=self.outlier_params,
                )
                phases = (
                    list(time_intervals.keys())
                    if time_intervals is not None
                    else ["Data"]
                )
                for phase in phases:
                    rsp_signal = ep.ecg_estimate_rsp(
                        ep, key=phase, edr_type=self.estimate_rsp_method
                    )
                    rsp_rate = RspProcessor.rsp_compute_rate(
                        rsp_signal, sampling_rate=self.sampling_rate
                    )
                    self.rsp_processor[subject] = {phase: (rsp_signal, rsp_rate)}
        else:
            self.rsp_processor = {}
            for subject in self.data.keys():
                time_intervals = self.get_timelog(subject)
                rp = RspProcessor(
                    data=self.data[subject],
                    sampling_rate=self.sampling_rate,
                    time_intervals=time_intervals,
                )
                rsp_rate = rp.rsp_compute_rate(
                    self.data[subject], sampling_rate=self.sampling_rate
                )
                self.rsp_processor[subject] = {"Data": (self.data[subject], rsp_rate)}
        self.data_processed = True

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
        if self.sampling_rate == -1:
            pn.state.notifications.error("Bitte eine sampling Rate eingeben")
            return
        for subject in list(self.data.keys()):
            time_intervals = (
                self.get_timelog(subject) if self.subject_time_dict else None
            )
            self.eeg_processor[subject] = EegProcessor(
                data=self.data[subject],
                sampling_rate=float(self.sampling_rate),
                time_intervals=time_intervals,
            )
            self.eeg_processor[subject].relative_band_energy(
                freq_bands=self.freq_bands, title=subject
            )
        self.data_processed = True
        return col

    def process_ecg(self):
        col = pn.Column()
        self.ecg_processor = {}
        for subject in self.data.keys():
            ep = EcgProcessor(
                data=self.data[subject],
                sampling_rate=self.sampling_rate,
                time_intervals=self.get_timelog(subject),
            )
            ep.ecg_process(
                outlier_correction=self.selected_outlier_methods,
                outlier_params=self.outlier_params,
            )
            self.ecg_processor[subject] = ep
        # elif self.session == "Multiple Sessions":
        #     self.ecg_processor = {}
        #     for subject in self.data.keys():
        #         ep = EcgProcessor(
        #             data=self.data[subject],
        #             sampling_rate=self.sampling_rate,
        #             time_intervals=self.get_timelog(subject),
        #         )
        #         ep.ecg_process(
        #             outlier_correction=self.selected_outlier_methods,
        #             outlier_params=self.outlier_params,
        #             title=subject,
        #         )
        #         self.ecg_processor[subject] = ep
        subject_result_dict = {}
        graph_dict = {}
        for subject in self.ecg_processor.keys():
            subject_result_dict[subject] = {
                "ECG Result": self.ecg_processor[subject].ecg_result,
                "Heart Rate Result": self.ecg_processor[subject].heart_rate,
                "HRV Result": self.ecg_processor[subject].hr_result,
            }
            graph_dict[subject] = self.ecg_processor[subject]
        self.result_view.set_subject_results(subject_result_dict)
        self.result_graph.set_signal(graph_dict)
        return col

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
        for subject in list(self.ecg_processor.keys()):
            self.dict_hr_subjects[subject] = {}
            for key in self.ecg_processor[subject].ecg_result.keys():
                self.dict_hr_subjects[subject][key] = self.ecg_processor[
                    subject
                ].hrv_process(
                    self.ecg_processor[subject],
                    key,
                    index=subject,
                    hrv_types=self.hrv_types.value,
                    correct_rpeaks=self.correct_rpeaks.value,
                )

    def panel(self):
        self.results = self.processing()
        self.result_graph.set_signal_type(self.signal)
        self.result_graph.set_sampling_rate(self.sampling_rate)
        return self._view
