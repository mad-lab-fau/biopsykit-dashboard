import zipfile
import biopsykit as bp
import pandas as pd
import panel as pn
import io

from src.Sleep.SLEEP_CONSTANTS import DOWNLOAD_SLEEP_RESULTS_TEXT
from src.Sleep.sleep_base import SleepBase


class DownloadSleepResults(SleepBase):
    load_results_btn = pn.widgets.Button(name="Download Results", button_type="primary")
    zip_buffer = io.BytesIO()
    download = pn.widgets.FileDownload(
        name="Load Sleep Results",
        filename="Results.zip",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = DOWNLOAD_SLEEP_RESULTS_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(DOWNLOAD_SLEEP_RESULTS_TEXT)
        self.download.callback = pn.bind(self.load_results)
        self._view = pn.Column(
            self.header,
            self.download,
        )

    def load_results(self):
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            for result in self.processed_data:
                for key in result.keys():
                    if isinstance(result[key], dict):
                        df = pd.DataFrame.from_dict(result[key])
                        df.to_excel(f"{key}.xlsx")
                        zip_file.write(f"{key}.xlsx")
                    elif isinstance(result[key], pd.DataFrame):
                        result[key].to_excel(f"{key}.xlsx")
                        zip_file.write(f"{key}.xlsx")
        self.zip_buffer.seek(0)
        return self.zip_buffer

    def panel(self):
        self.download.callback = pn.bind(self.load_results)
        self.download.filename = "Results.zip"
        self.download.name = "Download Results"
        self.download.param.update()
        return self._view
