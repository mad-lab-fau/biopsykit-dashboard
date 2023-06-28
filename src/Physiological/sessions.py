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
    ready = param.Boolean(default=True)
    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )
    selected_signal = param.String()

    def __init__(self):
        super().__init__()
        self.ready = True
        self._select = pn.widgets.Select.from_param(self.param.session)

    def panel(self):
        self.set_progress_value(self.progress_step)
        return pn.Column(
            pn.Row(self.get_step_static_text(self.progress_step)),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            self._select,
        )

    @param.output(
        ("selected_session", param.Dynamic),
        ("next_step", param.Integer),
        ("selected_signal", param.String),
    )
    def output(self):
        return (
            self.session,
            self.progress_step + 1,
            self.selected_signal,
        )
