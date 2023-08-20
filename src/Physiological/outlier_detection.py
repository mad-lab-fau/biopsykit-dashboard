import param
import panel as pn

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToDetectOutliers(PhysiologicalBase):
    data = param.Dynamic()
    sampling_rate = param.Number()
    skip_hrv = param.Boolean(default=True)
    session = param.String()
    sensors = param.Dynamic()
    timezone = param.String()
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    subject = param.Dynamic()
    subject_time_dict = param.Dynamic()

    next = param.Selector(
        default="Do you want to process the HRV also?",
        objects=["Do you want to process the HRV also?", "Expert Outlier Detection"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="Skip")
    expert_mode_btn = pn.widgets.Button(
        name="Expert Mode",
        button_type="warning",
    )
    default_btn = pn.widgets.Button(name="Default", button_type="primary")
    methods = [
        "quality",
        "artifact",
        "physiological",
        "statistical_rr",
        "statistical_rr_diff",
    ]
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=methods
    )

    statistical_param = pn.widgets.FloatInput(name="Statistical:", value=2.576)
    correlation = pn.widgets.FloatInput(name="correlation", value=0.3)
    quality = pn.widgets.FloatInput(name="quality", value=0.4)
    artifact = pn.widgets.FloatInput(name="artifact", value=0)
    statistical_rr = pn.widgets.FloatInput(name="statistical_rr", value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name="statistical_rr_diff", value=1.96)
    physiological_upper = pn.widgets.IntInput(name="physiological_upper", value=200)
    physiological_lower = pn.widgets.IntInput(name="physiological_lower", value=45)
    skip_outlier_detection = param.Boolean(default=True)
    outlier_params = param.Dynamic()

    def __init__(self):
        super().__init__()
        self.step = 7
        text = "# Do you want to check for outliers?"
        self.set_progress_value(self.step)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_detect_outlier})
        self._view = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(pn.Row(self.get_progress(self.step))),
            pn.pane.Markdown(text),
            pn.Row(self.skip_btn, self.default_btn, self.expert_mode_btn),
        )

    def click_skip(self, target, event):
        self.next = "Do you want to process the HRV also?"
        self.skip_outlier_detection = True
        self.ready = True

    def click_detect_outlier(self, target, event):
        self.next = "Expert Outlier Detection"
        self.skip_outlier_detection = False
        self.ready = True

    def click_default(self, event):
        self.next = "Do you want to process the HRV also?"
        self.skip_outlier_detection = False
        self.ready = True

    def get_outlier_params(self):
        self.outlier_params = {
            "correlation": self.correlation.value,
            "quality": self.quality.value,
            "artifact": self.artifact.value,
            "statistical_rr": self.statistical_rr.value,
            "statistical_rr_diff": self.statistical_rr_diff,
            "physiological": (
                self.physiological_lower.value,
                self.physiological_upper.value,
            ),
        }
        return self.outlier_params

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("timezone", param.String()),
        ("subject_time_dict", param.Dynamic),
        ("outlier_params", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.timezone,
            self.subject_time_dict,
            self.get_outlier_params(),
        )

    def panel(self):
        return self._view


class OutlierDetection(AskToDetectOutliers):
    textHeader = ""
    textParams = ""

    sensors = param.Dynamic()

    ecg_processor = None

    time_log = param.Dynamic()
    time_log_present = param.Boolean()

    outlier_params = param.Dynamic()

    def panel(self):
        self.step = 6
        # self.max_steps = 22
        self.set_progress_value(self.step)
        if self.textHeader == "":
            f = open("../assets/Markdown/OutlierDetection.html", "r")
            fileString = f.read()
            self.textHeader = fileString
        if self.textParams == "":
            f = open("../assets/Markdown/OutlierParams.md", "r")
            fileString = f.read()
            self.textParams = fileString
        return pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.progress),
            pn.pane.HTML(self.textHeader),
            self.outlier_methods,
            pn.pane.Markdown(self.textParams),
            self.correlation,
            self.quality,
            self.artifact,
            self.statistical_rr,
            self.statistical_rr_diff,
            pn.Row(self.physiological_lower, self.physiological_upper),
        )

    @pn.depends("physiological_upper.value", watch=True)
    def check_upper_bound(self):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            self.physiological_lower.value = self.physiological_upper.value

    @pn.depends("physiological_lower.value", watch=True)
    def check_lower_bound(self):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            self.physiological_upper.value = self.physiological_lower.value

    @param.output(
        ("outlier_params", param.Dynamic),
    )
    def output(self):
        return self.get_outlier_params()

    # @param.output(
    #     ("data", param.Dynamic),
    #     ("sampling_rate", param.Dynamic),
    #     ("outlier_params", param.Dynamic),
    #     ("outlier_methods", param.Dynamic),
    #     ("sensors", param.Dynamic),
    #     ("time_log_present", param.Dynamic),
    #     ("time_log", param.Dynamic),
    # )
    # def output(self):
    #     return (
    #         self.data,
    #         self.sampling_rate,
    #         self.get_outlier_params(),
    #         self.outlier_methods.value,
    #         self.sensors,
    #         self.time_log_present,
    #         self.time_log,
    #     )
