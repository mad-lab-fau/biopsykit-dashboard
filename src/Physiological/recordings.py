import panel as pn
import param

from src.Physiological.CONSTANTS import RECORDINGS_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Recordings(PhysiologicalBase):

    recording = param.Selector(
        default="Single Recording",
        objects=["Multiple Recording", "Single Recording"],
        label="Select recording type",
    )
    next = param.Selector(
        default="Upload Files", objects=["Upload Files", "Multiple Files"]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = RECORDINGS_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.ready = True
        self._select = pn.widgets.Select.from_param(self.param.recording)
        self._select.link(self, callbacks={"value": self.chg})
        self._view = pn.Column(
            self.header,
            self._select,
        )

    def chg(self, target, event):
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        return self._view
