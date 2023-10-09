import param
import panel as pn

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import (
    OUTLIER_METHODS,
    OUTLIER_DETECTION_TEXT,
    ASK_DETECT_OUTLIER_TEXT,
)
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToDetectOutliers(PhysiologicalBase):
    next = param.Selector(
        default="Do you want to process the HRV also?",
        objects=["Do you want to process the HRV also?", "Expert Outlier Detection"],
    )
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(
        name="Skip", sizing_mode="stretch_width", button_type="default"
    )
    expert_mode_btn = pn.widgets.Button(
        name="Expert Mode", button_type="danger", sizing_mode="stretch_width"
    )
    default_btn = pn.widgets.Button(
        name="Default", button_type="primary", sizing_mode="stretch_width"
    )
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=OUTLIER_METHODS
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_DETECT_OUTLIER_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_detect_outlier})
        self.default_btn.link(self, callbacks={"clicks": self.click_default})
        self._view = pn.Column(
            self.header,
            pn.Row(self.default_btn, self.expert_mode_btn, self.skip_btn),
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
    outlier_methods = pn.widgets.MultiChoice(
        name="Methods", value=["quality", "artifact"], options=OUTLIER_METHODS
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = OUTLIER_DETECTION_TEXT
        super().__init__(**params)
        self.step = 6
        self.update_step(6)
        self.update_text(OUTLIER_DETECTION_TEXT)
        self.set_progress_value(self.step)
        self.physiological_upper.link(self, callbacks={"value": self.check_upper_bound})
        self.physiological_lower.link(self, callbacks={"value": self.check_lower_bound})
        self.outlier_methods.link(
            self, callbacks={"value": self.outlier_methods_changed}
        )
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

    def outlier_methods_changed(self, _, event):
        if len(event.new) == 0:
            self.selected_outlier_methods = None
        self.selected_outlier_methods = event.new

    def check_upper_bound(self, target, event):
        if self.physiological_upper.value < 0:
            self.physiological_upper.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            switched_value = self.physiological_lower.value
            self.physiological_lower.value = self.physiological_upper.value
            self.physiological_upper.value = switched_value

    def check_lower_bound(self, target, event):
        if self.physiological_lower.value < 0:
            self.physiological_lower.value = 0
        if self.physiological_lower.value > self.physiological_upper.value:
            switched_value = self.physiological_upper.value
            self.physiological_upper.value = self.physiological_lower.value
            self.physiological_lower.value = switched_value

    def panel(self):
        return self._view
