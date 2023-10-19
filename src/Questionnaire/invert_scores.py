import numpy as np
import panel as pn
import param
import biopsykit as bp

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import ASK_TO_INVERT_SCORES_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class AskToInvertScores(QuestionnaireBase):
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Invert scores",
        objects=["Invert scores", "Show Results"],
    )
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    invert_scores_btn = pn.widgets.Button(name="Yes")

    def skip_inverting(self, target, event):
        self.next_page = "Show Results"
        self.ready = True

    def invert_scores(self, target, event):
        self.next_page = "Invert scores"
        self.ready = True

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_INVERT_SCORES_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(ASK_TO_INVERT_SCORES_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_inverting})
        self.invert_scores_btn.link(self, callbacks={"clicks": self.invert_scores})
        self._view = pn.Column(
            self.header,
            pn.Row(self.invert_scores_btn, self.skip_btn),
        )

    def panel(self):
        return self._view


class InvertScores(QuestionnaireBase):
    questionnaire_selector = pn.widgets.Select(name="Select Questionnaire")
    select_all_checkbox = pn.widgets.Checkbox(
        name="Select All", value=False, visible=False
    )
    column_cross_selector = pn.widgets.CrossSelector(
        name="Select Column(s)", visible=False
    )
    invert_scores_btn = pn.widgets.Button(name="Invert the scores", visible=False)
    score_range_array_input = pn.widgets.ArrayInput(
        name="Score Range", value=np.array([0, 0]), visible=False
    )

    def questionnaire_changed(self, _, event):
        questionnaire = event.new
        if questionnaire == "" or questionnaire is None:
            self.select_all_checkbox.visible = False
            self.column_cross_selector.visible = False
            self.invert_scores_btn.visible = False
            self.score_range_array_input.visible = False
            return
        self.select_all_checkbox.value = False
        self.select_all_checkbox.visible = True
        self.column_cross_selector.options = self.dict_scores[questionnaire].to_list()
        self.column_cross_selector.height = min(
            400, 100 + len(self.data.columns.tolist()) * 5
        )
        self.column_cross_selector.visible = True
        self.score_range_array_input.value = np.array([0, 0])
        self.score_range_array_input.visible = True
        self.invert_scores_btn.visible = True

    def select_all_checked(self, _, event):
        if (
            event.new
            and self.questionnaire_selector.value is not None
            and self.questionnaire_selector.value != ""
        ):
            self.column_cross_selector.value = self.dict_scores[
                self.questionnaire_selector.value
            ].to_list()
        else:
            self.column_cross_selector.value = []
            self.select_all_checkbox.value = False

    def invert_scores(self, target, event):
        if len(self.column_cross_selector.value) == 0:
            pn.state.notifications.error(
                "You have to select at least one column to invert the scores"
            )
            return
        if len(self.score_range_array_input.value) != 2:
            pn.state.notifications.error(
                "You have to fill out the field Score Range in a format like : [1,2]"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data.copy()
        try:
            self.data_scaled = bp.questionnaires.utils.invert(
                data=self.data_scaled,
                score_range=self.score_range_array_input.value,
                cols=self.column_cross_selector.value,
                inplace=False,
            )
            pn.state.notifications.success(
                f"Successfully inverted the scores of the selected columns to the range {self.score_range_array_input.value}"
            )
        except Exception as e:
            pn.state.notifications.error(
                f"Error occured while inverting the selected columns: {e}"
            )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_INVERT_SCORES_TEXT
        super().__init__(**params)
        self.update_step(7)
        self.update_text(ASK_TO_INVERT_SCORES_TEXT)
        self.questionnaire_selector.link(
            self, callbacks={"value": self.questionnaire_changed}
        )
        self.select_all_checkbox.link(
            self, callbacks={"value": self.select_all_checked}
        )
        self.invert_scores_btn.link(self, callbacks={"clicks": self.invert_scores})
        self._view = pn.Column(
            self.header,
            self.questionnaire_selector,
            self.select_all_checkbox,
            self.column_cross_selector,
            self.invert_scores_btn,
        )

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        return self._view
