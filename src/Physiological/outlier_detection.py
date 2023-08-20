import param
import panel as pn

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToDetectOutliers(PhysiologicalBase):
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

    def panel(self):
        return self._view


class OutlierDetection(PhysiologicalBase):
    textHeader = ""
    textParams = ""

    methods = [
        "quality",
        "artifact",
        "physiological",
        "statistical_rr",
        "statistical_rr_diff",
    ]
    statistical_param = pn.widgets.FloatInput(name="Statistical:", value=2.576)
    correlation = pn.widgets.FloatInput(name="correlation", value=0.3)
    quality = pn.widgets.FloatInput(name="quality", value=0.4)
    artifact = pn.widgets.FloatInput(name="artifact", value=0)
    statistical_rr = pn.widgets.FloatInput(name="statistical_rr", value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name="statistical_rr_diff", value=1.96)
    physiological_upper = pn.widgets.IntInput(name="physiological_upper", value=200)
    physiological_lower = pn.widgets.IntInput(name="physiological_lower", value=45)
    skip_outlier_detection = param.Boolean(default=True)
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=methods
    )

    def __init__(self):
        super().__init__()
        self.step = 6
        text = (
            "# Outlier Detection \n\n"
            "# # In this stage the ECG signal will be processed. This will be done in three steps: "
            "Filtering, R-peak detection, Outlier correction. \n\n"
            "Below you can select the outlier correction methods, which consist of: \n"
            "- Correlation: Computes cross-correlation coefficient between every single beat and the average of all"
            " detected beats. Marks beats as outlier if cross-correlation coefficient is below a certain threshold. \n"
            "- Quality: Uses the ECG_Quality indicator is below a certain threshold. \n"
            "- Artifact: Artifact detection based on Berntson et al. (1990)."
            "- Physiological: Physiological outlier removal. "
            "Marks beats if their heart rate is above or below a threshold that "
            "is very unlikely to be achieved physiologically. \n"
            "- Statistical rr: Marks beats as outlier if the RR interval is above or below a certain threshold. \n"
            "Statistical outlier removal based on RR intervals. Marks beats as outlier if the "
            "intervals are within the xx% highest or lowest values. Values are removed based on the z-score; "
            "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); "
            "2.576 => 1% (0.5% highest, 0.5% lowest values). \n"
            "- Statistical rr diff: Statistical outlier removal based on successive differences "
            "of RR intervals. Marks beats as outlier if the difference of successive RR intervals "
            "are within the xx% highest or lowest heart rates. Values are removed based on the z-score; "
            "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); 2.576 => 1% "
            "(0.5% highest, 0.5% lowest values). \n"
            "Furthermore, you can set the parameters for the outlier detection methods you chose down below. "
            "If you don't change anything the default values for the corresponding method will be used. \n"
        )
        self.set_progress_value(self.step)
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(pn.Row(self.get_progress(self.step))))
        pane.append(pn.pane.Markdown(text))
        pane.append(
            pn.Column(
                self.outlier_methods,
                self.correlation,
                self.quality,
                self.artifact,
                self.statistical_rr,
                self.statistical_rr_diff,
                pn.Row(self.physiological_lower, self.physiological_upper),
            )
        )
        self._view = pane

    def panel(self):
        return self._view

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
