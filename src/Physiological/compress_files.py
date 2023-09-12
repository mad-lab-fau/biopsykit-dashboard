import panel as pn
import param

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import COMPRESS_FILES_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Compress(PhysiologicalBase):
    def __init__(self, **params):
        params["HEADER_TEXT"] = COMPRESS_FILES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self._view = pn.Column(
            self.header,
        )

    def panel(self):
        return self._view
