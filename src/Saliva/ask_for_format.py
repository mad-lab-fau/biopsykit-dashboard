import param
import panel as pn

from src.Saliva.SALIVA_CONSTANTS import ASK_FOR_FORMAT_TEXT
from src.Saliva.SalivaBase import SalivaBase


class AskForFormat(SalivaBase):
    format_selector = pn.widgets.Select(
        options=["", "Wide Format", "Plate Format"],
        name="Format",
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_FOR_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(ASK_FOR_FORMAT_TEXT)
        self.format_selector.link(self, callbacks={"value": self.format_changed})
        self._view = pn.Column(
            self.header,
            self.format_selector,
        )

    def format_changed(self, _, event):
        self.format = event.new
        self.ready = bool(event.new)

    def panel(self):
        return self._view
