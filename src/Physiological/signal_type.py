import panel as pn
import param
from src.Physiological.PHYSIOLOGICAL_CONSTANTS import (
    SIGNAL_TYPE_TEXT,
    PHYSIOLOGICAL_SIGNAL_OPTIONS,
)
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class PhysSignalType(PhysiologicalBase):
    ready = param.Boolean(default=False)
    pane = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = SIGNAL_TYPE_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(SIGNAL_TYPE_TEXT)
        select = pn.widgets.Select(
            name="Select Signal Type",
            options=PHYSIOLOGICAL_SIGNAL_OPTIONS,
        )
        select.link(self, callbacks={"value": self.signal_selected})
        self._view = pn.Column(self.header, select)

    def signal_selected(self, target, event):
        self.selected_signal = event.new
        if self.selected_signal != "":
            self.ready = True
        else:
            self.ready = False

    def panel(self):
        self.ready = False
        return self._view
