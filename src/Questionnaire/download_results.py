import io
import re
import zipfile

import param
import panel as pn
import biopsykit as bp


class DownloadQuestionnaireResults(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    results = param.Dynamic()
    load_results_btn = pn.widgets.Button(name="Download Results", button_type="primary")
    zip_buffer = io.BytesIO()

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
        text = "# Results"
        col = pn.Column()
        download = pn.widgets.FileDownload(
            name="Load Questionnaire Results",
            callback=self.load_results,
            filename="Results.zip",
        )
        col.append(pn.pane.Markdown(text))
        col.append(download)
        return col
