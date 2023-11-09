import param
import panel as pn

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import (
    PROCESS_HRV_TEXT,
    ASK_PROCESS_HRV_TEXT,
    HRV_METHODS,
)
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToProcessHRV(PhysiologicalBase):
    methods = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]
    skip_btn = pn.widgets.Button(name="Skip", sizing_mode="stretch_width")
    expert_mode_btn = pn.widgets.Button(
        name="Expert Mode", button_type="danger", sizing_mode="stretch_width"
    )
    default_btn = pn.widgets.Button(
        name="Default", button_type="primary", sizing_mode="stretch_width"
    )
    next_page = param.Selector(
        default="Set HRV Parameters",
        objects=["Set HRV Parameters", "Now the Files will be processed"],
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_PROCESS_HRV_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.default_btn.link(self, callbacks={"clicks": self.click_default_hrv})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_expert_hrv})
        self._view = pn.Column(
            self.header, pn.Row(self.default_btn, self.expert_mode_btn, self.skip_btn)
        )

    def click_skip(self, target, event):
        self.next_page = "Now the Files will be processed"
        self.skip_hrv = True
        self.ready = True

    def click_expert_hrv(self, target, event):
        self.next_page = "Set HRV Parameters"
        self.skip_hrv = False
        self.ready = True

    def click_default_hrv(self, target, event):
        self.next_page = "Now the Files will be processed"
        self.skip_hrv = False
        self.hrv_types = None
        self.correct_rpeaks = True
        self.hrv_index_name = None
        self.hrv_index = None
        self.ready = True

    def panel(self):
        return self._view


class SetHRVParameters(PhysiologicalBase):
    select_hrv_types = pn.widgets.MultiChoice(
        name="Methods", value=["hrv_time", "hrv_nonlinear"], options=HRV_METHODS
    )
    check_correct_rpeaks = pn.widgets.Checkbox(name="Correct RPeaks", value=True)
    set_hrv_index_name = pn.widgets.TextInput(name="Index Name", value="")
    ready = param.Boolean(default=False)

    def __init__(self):
        super().__init__()
        self.update_text(PROCESS_HRV_TEXT)
        self.update_step(7)
        self.select_hrv_types.link(
            self, callbacks={"value": self.hrv_types_selection_changed}
        )
        self.check_correct_rpeaks.link(
            self, callbacks={"value": self.correct_rpeaks_checked}
        )
        self.set_hrv_index_name.link(
            self, callbacks={"value": self.hrv_index_name_changed}
        )
        self._view = pn.Column(
            self.header,
            self.select_hrv_types,
            self.check_correct_rpeaks,
            self.set_hrv_index_name,
        )

    def hrv_index_name_changed(self, _, event):
        self.hrv_index_name = event.new

    def correct_rpeaks_checked(self, _, event):
        self.correct_rpeaks = event.new

    def hrv_types_selection_changed(self, _, event):
        self.hrv_types = event.new

    def panel(self):
        self.select_hrv_types.value = self.hrv_types
        self.check_correct_rpeaks.value = self.correct_rpeaks
        self.set_hrv_index_name.value = self.hrv_index_name
        return self._view
