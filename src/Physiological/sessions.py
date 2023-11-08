import panel as pn
import param
from biopsykit.signals.ecg import EcgProcessor
import biopsykit as bp
from src.Physiological.PHYSIOLOGICAL_CONSTANTS import SESSION_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.ecg_plotting import ecg_plot
import holoviews as hv


class Session(PhysiologicalBase):
    select_session = pn.widgets.Select(
        name="",
        value="Single Session",
        options=["Multiple Sessions", "Single Session"],
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = SESSION_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.select_session.link(self, callbacks={"value": self.signal_selected})
        self.update_text(SESSION_TEXT)
        pane = pn.Column(
            self.header,
            self.select_session,
        )
        self._view = pane

    def signal_selected(self, _, event):
        self.session = event.new
        self.ready = self.session != ""

    def panel(self):
        return self._view
