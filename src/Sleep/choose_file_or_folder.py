import panel as pn

from src.Sleep.SLEEP_CONSTANTS import ZIP_OR_FOLDER_TEXT
from src.Sleep.sleep_base import SleepBase


class ZipFolder(SleepBase):
    def __init__(self, **params):
        params["HEADER_TEXT"] = ZIP_OR_FOLDER_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(ZIP_OR_FOLDER_TEXT)
        self._view = pn.Column(self.header)

    def panel(self):
        return self._view
