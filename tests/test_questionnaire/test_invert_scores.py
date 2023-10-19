import pytest
import biopsykit as bp

from src.Questionnaire.invert_scores import AskToInvertScores, InvertScores
from tests.test_questionnaire.QuestionnaireBaseMethodsForTesting import init_scores


class TestInvertScores:
    @pytest.fixture
    def ask_to_invert_scores(self):
        ask_to_invert_scores = AskToInvertScores()
        return ask_to_invert_scores

    @pytest.fixture
    def invert_scores(self):
        invert_scores = InvertScores()
        invert_scores.data, invert_scores.dict_scores = init_scores()
        invert_scores.data_scaled = invert_scores.data.copy()
        return invert_scores

    def test_ask_to_invert_scores_constructor(self, ask_to_invert_scores):
        assert ask_to_invert_scores is not None
        assert ask_to_invert_scores.next_page == "Invert scores"
        assert ask_to_invert_scores.ready is False

    def test_ask_to_invert_scores_btn(self, ask_to_invert_scores):
        ask_to_invert_scores.invert_scores_btn.clicks += 1
        assert ask_to_invert_scores.next_page == "Invert scores"
        assert ask_to_invert_scores.ready is True
        ask_to_invert_scores.skip_btn.clicks += 1
        assert ask_to_invert_scores.next_page == "Show Results"
        assert ask_to_invert_scores.ready is True

    def test_invert_scores_constructor(self, invert_scores):
        assert invert_scores is not None
        invert_scores.panel()
        assert invert_scores.questionnaire_selector is not None
        assert invert_scores.questionnaire_selector.options is not None
        assert invert_scores.column_cross_selector is not None
        assert invert_scores.invert_scores_btn is not None
        assert invert_scores.score_range_array_input is not None

    def test_invert_scores_select_all_changed(self, invert_scores):
        assert invert_scores.data is not None
        invert_scores.select_all_checkbox.value = True
        assert invert_scores.column_cross_selector.value == []
        invert_scores.questionnaire_selector.value = "panas-pre"
        invert_scores.select_all_checkbox.value = True
        assert invert_scores.column_cross_selector.value is not None
        assert (
            invert_scores.column_cross_selector.value
            == invert_scores.dict_scores["panas-pre"].to_list()
        )

    def test_invert_scores(self, invert_scores):
        data_before = invert_scores.data_scaled.copy()
        invert_scores.questionnaire_selector.value = None
        invert_scores.invert_scores_btn.clicks += 1
        assert invert_scores.data_scaled.equals(data_before) is True
        invert_scores.questionnaire_selector.value = "panas-pre"
        invert_scores.invert_scores_btn.clicks += 1
        assert invert_scores.data_scaled.equals(data_before) is True
        invert_scores.score_range_array_input.value = [0, 200]
        invert_scores.invert_scores_btn.clicks += 1
        assert invert_scores.data_scaled.equals(data_before) is True
        invert_scores.column_cross_selector.value = ["PANAS_01_Pre"]
        invert_scores.invert_scores_btn.clicks += 1
        data_inverted = bp.questionnaires.utils.invert(
            data=data_before, score_range=[0, 200], cols=["PANAS_01_Pre"], inplace=False
        )
        assert invert_scores.data_scaled.equals(data_inverted) is True
