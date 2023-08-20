import param
import panel as pn

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class AskToProcessHRV(PhysiologicalBase):
    methods = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]
    hrv_types = pn.widgets.MultiChoice(
        name="Methods", value=["hrv_time", "hrv_nonlinear"], options=methods
    )
    correct_rpeaks = pn.widgets.Checkbox(name="Correct RPeaks", value=True)
    index = pn.widgets.TextInput(name="Index", value="")
    index_name = pn.widgets.TextInput(name="Index Name", value="")
    skip_btn = pn.widgets.Button(name="Skip")
    expert_mode_btn = pn.widgets.Button(
        styles={"background": "#d5433e"}, name="Expert Mode", button_type="success"
    )
    default_btn = pn.widgets.Button(name="Default", button_type="primary")
    next_page = param.Selector(
        default="Set HRV Parameters",
        objects=["Set HRV Parameters", "Now the Files will be processed"],
    )
    ready = param.Boolean(default=False)

    def __init__(self):
        super().__init__()
        self.step = 7
        text = (
            "# Processing HRV \n \n"
            "If you want to additionally process the Heart Rate variability, "
            "you can select the matching parameters and then "
            "hit the process button, and then proceed. "
            "Otherwise, you can skip this step and go to the next stage. \n \n"
        )
        self.set_progress_value(self.step)
        self.skip_btn.link(self, callbacks={"clicks": self.click_skip})
        self.default_btn.link(self, callbacks={"clicks": self.click_default_hrv})
        self.expert_mode_btn.link(self, callbacks={"clicks": self.click_expert_hrv})
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(pn.Row(self.get_progress(self.step))))
        pane.append(pn.pane.Markdown(text))
        pane.append((pn.Row(self.skip_btn, self.default_btn, self.expert_mode_btn)))
        self._view = pane

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
        self.ready = True

    def panel(self):
        return self._view


class SetHRVParameters(PhysiologicalBase):
    methods = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]
    hrv_types = pn.widgets.MultiChoice(
        name="Methods", value=["hrv_time", "hrv_nonlinear"], options=methods
    )
    correct_rpeaks = pn.widgets.Checkbox(name="Correct RPeaks", value=True)
    index = pn.widgets.TextInput(name="Index", value="")
    index_name = pn.widgets.TextInput(name="Index Name", value="")

    def __init__(self):
        super().__init__()
        text = (
            "# Processing HRV \n \n"
            "If you want to additionally process the Heart Rate variability, "
            "you can select the matching parameters and then hit the "
            "process button, and then proceed. Otherwise, you can skip "
            "this step and go to the next stage. "
        )
        self.step = 7
        pane = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.get_progress(self.step)),
            pn.pane.Markdown(text),
            self.hrv_types,
            self.correct_rpeaks,
            self.index,
            self.index_name,
        )
        self._view = pane

    def panel(self):
        return self._view
