import pytest

from src.Questionnaire.check_selected_questionnaires import CheckSelectedQuestionnaires
from tests.Questionnaire.QuestionnaireBaseMethodsForTesting import upload_questionnaire


@pytest.fixture
def check_selected_questionnaires():
    suggest_questionnaires = CheckSelectedQuestionnaires()
    suggest_questionnaires.data = upload_questionnaire()
    return suggest_questionnaires


def test_constructor_suggest_questionnaires(check_selected_questionnaires):
    assert check_selected_questionnaires is not None
    assert check_selected_questionnaires.data is not None


def test_suggest_questionnaires(check_selected_questionnaires):
    check_selected_questionnaires.data = upload_questionnaire()
    assert check_selected_questionnaires.data is not None
    check_selected_questionnaires.init_questionnaire_panel(True)
    assert check_selected_questionnaires.questionnaire_panel is not None
    assert check_selected_questionnaires.questionnaire_panel.objects is not None

