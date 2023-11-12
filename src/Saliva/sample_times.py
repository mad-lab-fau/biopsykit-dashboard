import param
import panel as pn

from src.Saliva.SALIVA_CONSTANTS import (
    ASK_TO_SET_SAMPLE_TIMES_TEXT,
    SET_SAMPLE_TIMES_TEXT,
)
from src.Saliva.SalivaBase import SalivaBase


class AskToSetSampleTimes(SalivaBase):
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Add Sample Times",
        objects=[
            "Add Sample Times",
            "Ask for Subject Condition List",
        ],
    )
    no_sample_times_btn = pn.widgets.Button(
        name="No", button_type="light", sizing_mode="stretch_width"
    )
    add_sample_times_btn = pn.widgets.Button(name="Yes", sizing_mode="stretch_width")

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_SET_SAMPLE_TIMES_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(ASK_TO_SET_SAMPLE_TIMES_TEXT)
        self.no_sample_times_btn.link(self, callbacks={"clicks": self.no_sample_times})
        self.add_sample_times_btn.link(
            self, callbacks={"clicks": self.add_sample_times}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.add_sample_times_btn, self.no_sample_times_btn),
        )

    def no_sample_times(self, _, event):
        self.next_page = "Ask for Subject Condition List"
        self.ready = True

    def add_sample_times(self, _, event):
        self.next_page = "Add Sample Times"
        self.ready = True

    def panel(self):
        return self._view


class SetSampleTimes(SalivaBase):
    sample_times_input = pn.widgets.ArrayInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = SET_SAMPLE_TIMES_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(SET_SAMPLE_TIMES_TEXT)
        self.sample_times_input.param.watch(self.sample_times_changed, "value")
        self._view = pn.Column(
            self.header,
            pn.pane.Markdown("# Enter the sample times"),
            self.sample_times_input,
        )

    def sample_times_changed(self, event):
        self.sample_times = event.new
        if self.sample_times is None or len(self.sample_times) == 0:
            self.ready = False
        else:
            self.ready = True

    def panel(self):
        self.sample_times_input.param.watch(self.sample_times_changed, "value")
        return pn.Column(
            pn.pane.Markdown("# Enter the sample times"),
            self.sample_times_input,
        )
