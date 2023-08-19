import panel as pn
import param

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class PhysSignalType(PhysiologicalBase):
    text = "# Selecting Physiological Signal Type"
    ready = param.Boolean(default=False)
    pane = pn.Column()
    options = ["", "ECG", "CFT", "RSP", "EEG"]
    selected_signal = param.Selector(
        default="", objects=options, label="Select Signal Type"
    )

    def __init__(self, **params):
        super().__init__(**params)
        self.step = 1
        self.set_progress_value(self.step)
        select = pn.widgets.Select.from_param(self.param.selected_signal)
        self._view = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            select,
        )

    @param.depends("selected_signal", watch=True)
    def signal_selected(self):
        if self.selected_signal != "":
            self.ready = True
        else:
            self.ready = False

    @param.output(
        ("selected_signal", param.String),
        ("progress_step", param.Integer),
    )
    def output(self):
        return (
            self.selected_signal,
            (self.step + 1),
        )

    def panel(self):
        return self._view
