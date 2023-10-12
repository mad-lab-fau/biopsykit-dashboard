import param
import panel as pn
import biopsykit as bp

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import SHOW_RESULTS_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class ShowResults(QuestionnaireBase):

    text = "# Show Results"
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Ask to change format"],
    )
    questionnaire_results_Column = pn.Column()

    def show_questionnaire_results(self) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width")
        supported_questionnaires = (
            bp.questionnaires.utils.get_supported_questionnaires()
        )
        for questionnaire in supported_questionnaires:
            questionnaire_results = self.results.filter(like=questionnaire.upper())
            if questionnaire_results.empty:
                continue
            tabulator = pn.widgets.Tabulator(
                questionnaire_results,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
            )
            acc.append(
                (
                    questionnaire,
                    tabulator,
                )
            )
        return acc

    def __init__(self, **params):
        params["HEADER_TEXT"] = SHOW_RESULTS_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(SHOW_RESULTS_TEXT)
        self._view = pn.Column(self.header, self.questionnaire_results_Column)

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        self.results = bp.questionnaires.utils.compute_scores(
            data=self.data_scaled, quest_dict=self.dict_scores
        )
        if all("_" in cols for cols in self.results.columns.to_list()):
            self.next_page = "Ask to change format"
        self.questionnaire_results_Column.__setitem__(
            0, self.show_questionnaire_results()
        )
        return self._view
