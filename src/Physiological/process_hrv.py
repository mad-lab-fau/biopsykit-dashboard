import param
import panel as pn

from src.Physiological.processing_and_preview import ProcessingAndPreview


class AskToProcessHRV(ProcessingAndPreview):
    methods = ["hrv_time", "hrv_nonlinear", "hrv_frequency", "all"]
    hrv_types = pn.widgets.MultiChoice(
        name="Methods", value=["hrv_time", "hrv_nonlinear"], options=methods
    )
    correct_rpeaks = pn.widgets.Checkbox(name="Correct RPeaks", value=True)
    index = pn.widgets.TextInput(name="Index", value="")
    index_name = pn.widgets.TextInput(name="Index Name", value="")
    skip_btn = pn.widgets.Button(name="Skip")
    expert_mode_btn = pn.widgets.Button(
        background="#d5433e", name="Expert Mode", button_type="success"
    )
    default_btn = pn.widgets.Button(name="Default", button_type="primary")
    # process_hrv_btn = pn.widgets.Button(name="Process HRV")
    next_page = param.Selector(
        default="Process HRV",
        objects=["Process HRV", "Results"],
    )
    ready = param.Boolean(default=False)
    skip_hrv = False

    def click_skip(self, event):
        self.next_page = "Results"
        self.skip_hrv = True
        self.ready = True

    def click_expert_hrv(self, event):
        self.next_page = "Process HRV"
        self.ready = True

    def click_default_hrv(self, event):
        self.next_page = "Process HRV"
        self.ready = True

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/ProcessHRV.md", "r")
            fileString = f.read()
            self.text = fileString
        self.skip_btn.on_click(self.click_skip)
        self.expert_mode_btn.on_click(self.click_expert_hrv)
        self.default_btn.on_click(self.click_default_hrv)
        return pn.Column(
            pn.pane.Markdown(self.text),
            pn.Row(self.skip_btn, self.expert_mode_btn, self.default_btn),
        )


class ProcessHRV(AskToProcessHRV):
    def process_hrv(self):
        keys = self.ecg_processor.ecg_result.keys()
        for key in keys:
            self.ecg_processor.hrv_process(
                self.ecg_processor,
                key,
                index=self.index.value,
                index_name=self.index_name.value,
                hrv_types=self.hrv_types.value,
                correct_rpeaks=self.correct_rpeaks.value,
            )
        pn.state.notifications.success("HRV processed successfully")

    def panel(self):
        if self.textHeader == "":
            f = open("../assets/Markdown/ProcessHRV.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        # self.process_btn.on_click(self.process_hrv)
        return pn.Column(
            pn.pane.Markdown(self.textHeader),
            self.hrv_types,
            self.correct_rpeaks,
            self.index,
            self.index_name,
            # self.sampling_rate,
        )
