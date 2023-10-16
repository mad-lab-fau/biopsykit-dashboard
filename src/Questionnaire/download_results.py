import io
import zipfile

import panel as pn
import biopsykit as bp

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import DOWNLOAD_RESULTS_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class DownloadQuestionnaireResults(QuestionnaireBase):
    load_results_btn = pn.widgets.Button(name="Download Results", button_type="primary")
    zip_buffer = io.BytesIO()
    download = pn.widgets.FileDownload(
        name="Load Questionnaire Results",
        filename="Results.zip",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = DOWNLOAD_RESULTS_TEXT
        super().__init__(**params)
        self.update_step(9)
        self.update_text(DOWNLOAD_RESULTS_TEXT)
        self.download.callback = pn.bind(self.load_results)
        self._view = pn.Column(
            self.header,
            self.download,
        )

    def load_results(self):
        with zipfile.ZipFile(
            self.zip_buffer, "a", zipfile.ZIP_DEFLATED, False
        ) as zip_file:
            supported_questionnaires = (
                bp.questionnaires.utils.get_supported_questionnaires()
            )
            for questionnaire in supported_questionnaires:
                questionnaire_results = self.results.filter(like=questionnaire.upper())
                if questionnaire_results.empty:
                    continue
                questionnaire_results.to_excel(
                    f"{questionnaire}_results_.xlsx",
                    sheet_name=questionnaire,
                )
                zip_file.write(f"{questionnaire}_results_.xlsx")
        self.zip_buffer.seek(0)
        return self.zip_buffer

    def panel(self):
        self.download.callback = pn.bind(self.load_results)
        self.download.filename = "Results.zip"
        self.download.name = "Download Results"
        self.download.param.update()
        return self._view
