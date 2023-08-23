import panel as pn
import param

from src.Physiological.CONSTANTS import SIGNAL_TYPE_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.custom_components import PipelineHeader


class PhysSignalType(PhysiologicalBase):
    ready = param.Boolean(default=False)
    pane = pn.Column()

    def __init__(self, **params):
        super().__init__(**params)
        self.step = 1
        self.update_text(SIGNAL_TYPE_TEXT)
        self.set_progress_value(self.step)
        select = pn.widgets.Select.from_param(self.param.selected_signal)
        select.link(self, callbacks={"value": self.signal_selected})
        self._view = pn.Column(
            self.header,
            select,
        )

    def signal_selected(self, target, event):
        if self.selected_signal != "":
            self.ready = True
        else:
            self.ready = False

    def panel(self):
        self.ready = False
        self.update_step(self.step)
        return self._view
