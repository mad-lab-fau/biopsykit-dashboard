import panel as pn

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import CHECK_SELECTED_QUESTIONNAIRES_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class CheckSelectedQuestionnaires(QuestionnaireBase):
    text = ""
    check_btn = pn.widgets.Button(
        name="Check Questionnaires", sizing_mode="stretch_width"
    )
    accordion = pn.Accordion(sizing_mode="stretch_width")
    questionnaire_panel = pn.Column(sizing_mode="stretch_width")

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHECK_SELECTED_QUESTIONNAIRES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(CHECK_SELECTED_QUESTIONNAIRES_TEXT)
        self.check_btn.link(self, callbacks={"clicks": self.check_questionnaires})
        self._view = pn.Column(
            self.header,
            self.check_btn,
            self.questionnaire_panel,
        )

    def init_questionnaire_panel(self, visible: bool) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width", visible=visible)
        for questionnaire in self.dict_scores.keys():
            df = self.data[list(self.dict_scores[questionnaire])]
            df_widget = pn.widgets.Tabulator(
                df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=20,
                header_align="right",
                theme="midnight",
            )
            acc.append((questionnaire, df_widget))
        return acc

    def check_questionnaires(self, _, event):
        acc = self.init_questionnaire_panel((event.new % 2) != 0)
        self.questionnaire_panel.__setitem__(0, acc)

    def panel(self):
        if len(self.questionnaire_panel.objects) > 0:
            return self._view
        self.questionnaire_panel.__setitem__(0, self.init_questionnaire_panel(False))
        return self.questionnaire_panel
