import param
import panel as pn
from biopsykit.signals.ecg import EcgProcessor

from src.Physiological.add_times import AskToAddTimes


class AskToDetectOutliers(AskToAddTimes):
    text = ""
    ready = param.Boolean(default=True)
    next = param.Selector(
        default="Now the Files will be processed",
        objects=["Now the Files will be processed", "Expert Processing"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="Skip")
    expert_mode_btn = pn.widgets.Button(
        background="#d5433e", name="Expert Mode", button_type="success"
    )
    default_btn = pn.widgets.Button(name="Default", button_type="primary")

    def click_skip(self, event):
        self.next = "Now the Files will be processed"
        self.ready = True

    def click_detect_outlier(self, event):
        self.next = "Expert Processing"
        self.ready = True

    def click_default(self, event):
        self.next = "Now the Files will be processed"
        self.ready = True

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/AskToDetectOutliers.md", "r")
            fileString = f.read()
            self.text = fileString
        self.expert_mode_btn.on_click(self.click_detect_outlier)
        self.skip_btn.on_click(self.click_skip)
        self.default_btn.on_click(self.click_default)
        return pn.Column(
            pn.Row(self.step),
            pn.pane.Markdown(self.text),
            pn.Row(self.skip_btn, self.default_btn, self.expert_mode_btn),
        )


class OutlierDetection(param.Parameterized):
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    textHeader = ""
    textParams = ""
    methods = [
        "quality",
        "artifact",
        "physiological",
        "statistical_rr",
        "statistical_rr_diff",
    ]
    sensors = param.Dynamic()
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=methods
    )
    statistical_param = pn.widgets.FloatInput(name="Statistical:", value=2.576)
    ecg_processor = None
    correlation = pn.widgets.FloatInput(name="correlation", value=0.3)
    quality = pn.widgets.FloatInput(name="quality", value=0.4)
    artifact = pn.widgets.FloatInput(name="artifact", value=0)
    statistical_rr = pn.widgets.FloatInput(name="statistical_rr", value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name="statistical_rr_diff", value=1.96)
    physiological_upper = pn.widgets.IntInput(name="physiological_upper", value=200)
    physiological_lower = pn.widgets.IntInput(name="physiological_lower", value=45)
    time_log = param.Dynamic()
    time_log_present = param.Boolean()

    def panel(self):

        if self.textHeader == "":
            f = open("../assets/Markdown/OutlierDetection.html", "r")
            fileString = f.read()
            self.textHeader = fileString
        if self.textParams == "":
            f = open("../assets/Markdown/OutlierParams.md", "r")
            fileString = f.read()
            self.textParams = fileString
        return pn.Column(
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

    def get_outlier_params(self):
        return {
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

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("outlier_params", param.Dynamic),
        ("outlier_methods", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.get_outlier_params(),
            self.outlier_methods.value,
            self.sensors,
            self.time_log_present,
            self.time_log,
        )
