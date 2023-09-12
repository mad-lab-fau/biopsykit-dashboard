import param
import panel as pn

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import SESSION_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Session(PhysiologicalBase):
    progress_step = param.Integer()
    session = param.Selector(
        label="Select session type",
        default="Single Session",
        objects=["Multiple Sessions", "Single Session"],
    )

    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )
    selected_signal = param.String()

    def __init__(self, **params):
        params["HEADER_TEXT"] = SESSION_TEXT
        super().__init__(**params)
        self.update_step(2)
        self._select = pn.widgets.Select.from_param(self.param.session)
        self.update_text(SESSION_TEXT)
        pane = pn.Column(
            self.header,
            self._select,
        )
        self._view = pane

    def panel(self):
        return self._view
