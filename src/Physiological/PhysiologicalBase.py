import pandas as pd
import param
import panel as pn
import datetime as datetime

from biopsykit.signals.ecg import EcgProcessor

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import *
from src.Physiological.custom_components import PipelineHeader


class PhysiologicalBase(param.Parameterized):
    artifact = param.Dynamic(default=0.0)
    correlation = param.Dynamic(default=0.3)
    correct_rpeaks = param.Boolean(default=True)
    cft_sheets = param.Dynamic()
    cft_processor = {}
    data = param.Dynamic()
    data_processed = param.Boolean(default=False)
    default_outlier_detection = param.Boolean(default=False)
    dict_hr_subjects = {}
    ecg_processor = param.Dynamic()
    eeg_processor = {}
    estimate_rsp = param.Boolean(default=False)
    estimate_rsp_method = param.String(default="peak_trough_mean")
    freq_bands = param.Dynamic(default=None)
    hardware = param.Selector(
        label="Select the Hardware with which you recorded your data",
        objects=PHYSIOLOGICAL_HW_OPTIONS,
        default="NilsPod",
    )
    hr_data = None
    hrv_types = param.List(default=None)
    hrv_index_name = param.Dynamic(default=None)
    hrv_index = param.Dynamic(default=None)
    original_data = param.Dynamic()
    progress = pn.indicators.Progress(
        name="Progress", height=20, sizing_mode="stretch_width"
    )
    phase_series = param.Dynamic()
    physiological_upper = param.Integer(default=200)
    physiological_lower = param.Integer(default=40)
    quality = param.Dynamic(default=0.4)
    recording = param.String(default="Single Recording")
    rsp_processor = {}
    sampling_rate = param.Number(default=-1.0)
    synced = param.Boolean(default=False)
    skip_hrv = param.Boolean(default=True)
    session = param.String(default="Single Session")
    sensors = param.Dynamic()
    subject = param.Dynamic()
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )
    signal = param.String(default="")
    step = param.Integer(default=1)
    subject_time_dict = param.Dynamic(default={})
    statistical_param = pn.widgets.FloatInput(name="Statistical:", value=2.576)
    statistical_rr = param.Dynamic(default=2.576)
    statistical_rr_diff = param.Dynamic(default=1.96)
    skip_outlier_detection = param.Boolean(default=True)
    outlier_methods = param.Dynamic(default=None)
    textHeader = ""
    times = None
    timezone = param.String(default="Europe/Berlin")
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    trimmed_data = param.Dynamic()
    max_steps = PHYSIOLOGICAL_MAX_STEPS
    outlier_params = param.Dynamic(default=None)

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, PHYSIOLOGICAL_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    @staticmethod
    def get_progress(step) -> pn.indicators.Progress:
        return pn.indicators.Progress(
            name="Progress", height=20, sizing_mode="stretch_width", max=12, value=step
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)

    def select_vp_changed(self, _, event):
        self.subject = str(event.new)

    def dict_to_column(self):
        if self.session == "Single Session" and len(self.subject_time_dict.keys()) > 1:
            self.select_vp.options = list(self.subject_time_dict.keys())
            self.select_vp.visible = True
            self.select_vp.link(
                "subject",
                callbacks={"value": self.select_vp_changed},
            )
            self.subject = list(self.subject_time_dict.keys())[0]
            self.ready = True
        timestamps = []
        for subject in self.subject_time_dict.keys():
            col = pn.Column()
            for condition in self.subject_time_dict[subject].keys():
                cond = pn.widgets.TextInput(value=condition)
                cond.link(
                    (subject, condition),
                    callbacks={"value": self.change_condition_name},
                )
                btn_remove_phase = pn.widgets.Button(
                    name="Remove Phase", button_type="danger"
                )
                btn_remove_phase.link(
                    (subject, condition),
                    callbacks={"value": self.remove_btn_click},
                )
                col.append(pn.Row(cond, btn_remove_phase))
                for phase, time in self.subject_time_dict[subject][condition].items():
                    row = pn.Row()
                    phase_name_input = pn.widgets.TextInput(value=phase)
                    phase_name_input.link(
                        (subject, condition, phase),
                        callbacks={"value": self.change_phase_name},
                    )
                    row.append(phase_name_input)
                    dt_picker = pn.widgets.DatetimePicker(value=time)
                    dt_picker.link(
                        (subject, condition, phase),
                        callbacks={"value": self.timestamp_changed},
                    )
                    row.append(dt_picker)
                    remove_btn = pn.widgets.Button(name="Remove", button_type="danger")
                    remove_btn.link(
                        (subject, condition, phase),
                        callbacks={"value": self.remove_btn_click},
                    )
                    row.append(remove_btn)
                    col.append(row)
                btn_subphase = pn.widgets.Button(
                    name="Add Subphase", button_type="primary"
                )
                btn_subphase.link(
                    (subject, condition),
                    callbacks={"value": self.add_subphase_btn_click},
                )
                row = pn.Row(pn.layout.HSpacer(), pn.layout.HSpacer(), btn_subphase)
                col.append(row)
            btn = pn.widgets.Button(name="Add Phase", button_type="primary")
            btn.link(
                (subject,),
                callbacks={"value": self.add_phase_btn_click},
            )
            col.append(btn)
            timestamps.append((subject, col))
        self.times.objects = [pn.Accordion(objects=timestamps)]

    def add_phase_btn_click(self, target, _):
        new_phase_name = "New Phase"
        self.subject_time_dict[target[0]][new_phase_name] = pd.Series(
            {"New Subphase": datetime.datetime.now()}
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

    def add_subphase_btn_click(self, target, event):
        new_phase_name = "New Subphase"
        if new_phase_name in list(
            self.subject_time_dict[target[0]][target[1]].index.values
        ):
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in list(
                self.subject_time_dict[target[0]][target[1]].index.values
            ):
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
        self.subject_time_dict[target[0]][target[1]] = pd.concat(
            [
                self.subject_time_dict[target[0]][target[1]],
                pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
            ]
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

    def get_outlier_params(self):
        if self.skip_outlier_detection:
            self.outlier_params = None
            self.outlier_methods = None
            return None
        if self.default_outlier_detection:
            return EcgProcessor.outlier_params_default()
        self.outlier_params = {
            "correlation": self.correlation,
            "quality": self.quality,
            "artifact": self.artifact,
            "statistical_rr": self.statistical_rr,
            "statistical_rr_diff": self.statistical_rr_diff,
            "physiological": (
                self.physiological_lower,
                self.physiological_upper,
            ),
        }
        return self.outlier_params

    @param.output(
        ("freq_bands", param.Dynamic),
        ("synced", param.Boolean),
        ("subject_time_dict", param.Dynamic),
        ("timezone", param.String()),
        ("trimmed_data", param.Dynamic),
        ("session", param.String),
        ("selected_signal", param.String),
        ("recording", param.String),
        ("data", param.Dynamic),
        ("sampling_rate", param.Number),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Boolean),
        ("time_log", param.Dynamic),
        ("outlier_params", param.Dynamic),
        ("selected_outlier_methods", param.Dynamic),
        ("skip_hrv", param.Boolean),
        ("subject", param.Dynamic),
        ("cft_sheets", param.Dynamic),
        ("phase_series", param.Dynamic),
    )
    def output(self):
        return (
            self.freq_bands,
            self.synced,
            self.subject_time_dict,
            self.timezone,
            self.trimmed_data,
            self.session,
            self.signal,
            self.recording,
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.get_outlier_params(),
            self.outlier_methods,
            self.skip_hrv,
            self.subject,
            self.cft_sheets,
            self.phase_series,
        )
