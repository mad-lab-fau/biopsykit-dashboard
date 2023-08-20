import panel as pn
import param

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class PhysSignalType(PhysiologicalBase):
    text = "# Selecting Physiological Signal Type"
    ready = param.Boolean(default=False)
    pane = pn.Column()

    def __init__(self, **params):
        super().__init__(**params)
        self.step = 1
        self.set_progress_value(self.step)
        select = pn.widgets.Select.from_param(self.param.selected_signal)
        select.link(self, callbacks={"value": self.signal_selected})
        self._view = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.get_progress(self.step)),
            pn.pane.Markdown(self.text),
            select,
        )

    def signal_selected(self, target, event):
        if self.selected_signal != "":
            self.ready = True
        else:
            self.ready = False

    def panel(self):
        self.ready = False
        return self._view
