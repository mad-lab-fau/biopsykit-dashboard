import os

import pytest

from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from src.Questionnaire.upload_questionnaire_data import UploadQuestionnaireData


def upload_questionnaire():
    upload_data = UploadQuestionnaireData()
    upload_data.file_input.filename = "questionnaire.csv"
    with open(
        os.path.join(os.path.dirname(__file__), "example_data", "questionnaire.csv"),
        "rb",
    ) as f:
        upload_data.file_input.value = f.read()
    return upload_data.data


@pytest.fixture
def suggest_questionnaires():
    suggest_questionnaires = SuggestQuestionnaireScores()
    suggest_questionnaires.data = upload_questionnaire()
    return suggest_questionnaires


def test_constructor_suggest_questionnaires(suggest_questionnaires):
    assert suggest_questionnaires is not None
    assert suggest_questionnaires.data is not None
    assert suggest_questionnaires.select_questionnaire is not None
    assert suggest_questionnaires.add_questionnaire_btn is not None
    assert suggest_questionnaires.accordion is not None


def test_init_suggest_questionnaire(suggest_questionnaires):
    suggest_questionnaires.init_dict_scores()
    assert suggest_questionnaires.dict_scores is not None
    assert len(suggest_questionnaires.dict_scores) > 0
    assert suggest_questionnaires.dict_scores["panas-pre"] is not None
    assert suggest_questionnaires.dict_scores["panas-post"] is not None
    assert suggest_questionnaires.dict_scores["pasa"] is not None
    assert suggest_questionnaires.dict_scores["pss"] is not None


def test_add_questionnaire(suggest_questionnaires):
    suggest_questionnaires.init_dict_scores()
    suggest_questionnaires.select_questionnaire.value = "abi"
    suggest_questionnaires.add_questionnaire_btn.clicks += 1
    assert "abi" in list(suggest_questionnaires.dict_scores.keys())
    suggest_questionnaires.add_questionnaire_btn.clicks += 1
    assert "abi-New0" in list(suggest_questionnaires.dict_scores.keys())


def test_remove_questionnaire(suggest_questionnaires):
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
