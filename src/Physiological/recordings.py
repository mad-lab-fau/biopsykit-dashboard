import panel as pn
import param

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import RECORDINGS_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Recordings(PhysiologicalBase):
    select_recording = pn.widgets.Select(
        options=["Multiple Recording", "Single Recording"],
        name="Select recording type",
        value="Single Recording",
        sizing_mode="stretch_width",
    )
    next = param.Selector(
        default="Upload Files", objects=["Upload Files", "Multiple Files"]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = RECORDINGS_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.select_recording.link(self, callbacks={"value": self.chg})
        self._view = pn.Column(
            self.header,
            self.select_recording,
        )

    def chg(self, _, event):
        self.recording = event.new
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        return self._view
