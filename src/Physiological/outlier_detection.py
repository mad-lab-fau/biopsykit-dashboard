import param
import panel as pn

from src.Physiological.CONSTANTS import (
    OUTLIER_METHODS,
    ASK_PROCESS_HRV_TEXT,
    OUTLIER_DETECTION_TEXT,
)
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
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=OUTLIER_METHODS
    )

    def __init__(self):
        super().__init__()
        self.step = 7
        self.update_step(7)
        self.update_text(ASK_PROCESS_HRV_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_detect_outlier})
        self.default_btn.link(self, callbacks={"clicks": self.click_default})
        self._view = pn.Column(
            self.header,
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

    def click_default(self, target, event):
        self.next = "Do you want to process the HRV also?"
        self.skip_outlier_detection = False
        self.ready = True

    def panel(self):
        return self._view


class OutlierDetection(PhysiologicalBase):
    textHeader = ""

    def __init__(self):
        super().__init__()
        self.step = 6
        self.update_step(6)
        self.update_text(OUTLIER_DETECTION_TEXT)
        self.set_progress_value(self.step)
        self.physiological_upper.link(self, callbacks={"value": self.check_upper_bound})
        self.physiological_lower.link(self, callbacks={"value": self.check_lower_bound})
        pane = pn.Column(self.header)
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

    def check_upper_bound(self):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            self.physiological_lower.value = self.physiological_upper.value

    def check_lower_bound(self):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            self.physiological_upper.value = self.physiological_lower.value

    def panel(self):
        return self._view
