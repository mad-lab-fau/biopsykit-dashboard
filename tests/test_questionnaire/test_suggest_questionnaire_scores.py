import pytest

from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from tests.test_questionnaire.QuestionnaireBaseMethodsForTesting import (
    upload_questionnaire,
)


class TestSuggestQuestionnaireScores:
    @pytest.fixture
    def suggest_questionnaires(self):
        suggest_questionnaires = SuggestQuestionnaireScores()
        suggest_questionnaires.data = upload_questionnaire()
        return suggest_questionnaires

    def test_constructor_suggest_questionnaires(self, suggest_questionnaires):
        assert suggest_questionnaires is not None
        assert suggest_questionnaires.data is not None
        assert suggest_questionnaires.select_questionnaire is not None
        assert suggest_questionnaires.add_questionnaire_btn is not None
        assert suggest_questionnaires.accordion is not None

    def test_init_suggest_questionnaire(self, suggest_questionnaires):
        suggest_questionnaires.init_dict_scores()
        assert suggest_questionnaires.dict_scores is not None
        assert len(suggest_questionnaires.dict_scores) > 0
        assert suggest_questionnaires.dict_scores["panas-pre"] is not None
        assert suggest_questionnaires.dict_scores["panas-post"] is not None
        assert suggest_questionnaires.dict_scores["pasa"] is not None
        assert suggest_questionnaires.dict_scores["pss"] is not None

    def test_add_questionnaire(self, suggest_questionnaires):
        suggest_questionnaires.init_dict_scores()
        suggest_questionnaires.select_questionnaire.value = "abi"
        suggest_questionnaires.add_questionnaire_btn.clicks += 1
        assert "abi" in list(suggest_questionnaires.dict_scores.keys())
        suggest_questionnaires.add_questionnaire_btn.clicks += 1
        assert "abi-New0" in list(suggest_questionnaires.dict_scores.keys())

    def test_remove_questionnaire(self, suggest_questionnaires):
        suggest_questionnaires.init_dict_scores()
        suggest_questionnaires.show_dict_scores()
        assert suggest_questionnaires.dict_scores["panas-pre"] is not None
        len_before_removal = len(suggest_questionnaires.accordion.objects)
        suggest_questionnaires.remove_questionnaire("panas-pre", None)
        assert "panas-pre" not in list(suggest_questionnaires.dict_scores.keys())
        assert len(suggest_questionnaires.accordion.objects) == len_before_removal - 1
        len_before_removal = len(suggest_questionnaires.accordion.objects)
        suggest_questionnaires.remove_questionnaire("not a questionnaire", None)
        assert len(suggest_questionnaires.accordion.objects) == len_before_removal
