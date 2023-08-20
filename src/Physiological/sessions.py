import param
import panel as pn

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Session(PhysiologicalBase):
    progress_step = param.Integer()
    session = param.Selector(
        label="Select session type",
        default="Single Session",
        objects=["Multiple Sessions", "Single Session"],
    )
    text = (
        "# Number of Sessions \n"
        "In this step you can define if your data consists of a single Session or multiple Sessions. \n\n"
        "In this context a single Session is defined that only one Sensor is used, "
        "while multiple Sessions describe that two or more sensors are used. \n"
    )
    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )
    selected_signal = param.String()

    def __init__(self):
        super().__init__()
        self.step = 2
        self._select = pn.widgets.Select.from_param(self.param.session)
        pane = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.get_progress(self.step)),
            pn.pane.Markdown(self.text),
            self._select,
        )
        self._view = pane

    def panel(self):
        return self._view
