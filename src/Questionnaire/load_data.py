from io import StringIO

import param
import panel as pn

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import LOADING_DATA_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase
from src.utils import load_questionnaire_data


class LoadQuestionnaireData(QuestionnaireBase):
    text = ""
    ready = param.Boolean(default=False)
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xls,.xlsx",
    )

    def parse_file_input(self, _, event):
        try:
            pn.state.notifications.info("Loading data")
            self.data = load_questionnaire_data(
                file=self.file_input.value,
                file_name=self.file_input.filename,
                subject_col=self.subject_col,
                condition_col=self.condition_col,
                additional_index_cols=self.additional_index_cols,
                replace_missing_vals=self.replace_missing_vals,
                remove_nan_rows=self.remove_nan_rows,
                sheet_name=self.sheet_name,
            )
            self.ready = True
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOADING_DATA_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(LOADING_DATA_TEXT)
        self.file_input.link(self, callbacks={"clicks": self.parse_file_input})
        self._view = pn.Column(
            self.header,
            self.file_input,
        )

    def panel(self):
        return self._view
