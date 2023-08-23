import panel as pn
import param

from src.Physiological.CONSTANTS import COMPRESS_FILES_TEXT
from src.Physiological.recordings import Recordings


class Compress(Recordings):
    def __init__(self):
        super().__init__()
        self.step = 4
        self.update_step(4)
        self.update_text(COMPRESS_FILES_TEXT)
        self.set_progress_value(self.step)
        self._view = pn.Column(
            self.header,
        )

    def panel(self):
        return self._view
