import panel as pn
import param
from src.Physiological.PHYSIOLOGICAL_CONSTANTS import (
    SIGNAL_TYPE_TEXT,
    PHYSIOLOGICAL_SIGNAL_OPTIONS,
)
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class PhysSignalType(PhysiologicalBase):
    ready = param.Boolean(default=False)
    select_signal = pn.widgets.Select(
        name="Select Signal Type",
        options=PHYSIOLOGICAL_SIGNAL_OPTIONS,
        sizing_mode="stretch_width",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SIGNAL_TYPE_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(SIGNAL_TYPE_TEXT)
        self.select_signal.link(self, callbacks={"value": self.signal_selected})
        self._view = pn.Column(self.header, self.select_signal)

    def signal_selected(self, _, event):
        self.signal = event.new if event.new in PHYSIOLOGICAL_SIGNAL_OPTIONS else ""
        if self.signal != "":
            self.ready = True
        else:
            self.ready = False

    def panel(self):
        self.ready = False
        return self._view
