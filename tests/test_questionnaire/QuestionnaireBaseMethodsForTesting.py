import os
from pathlib import Path

from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from src.Questionnaire.upload_questionnaire_data import UploadQuestionnaireData


def script_dir():
    full_path = os.path.dirname(__file__)
    directory = str(Path(full_path).parents[0])
    return os.path.join(directory, "test_data")


def upload_questionnaire():
    upload_data = UploadQuestionnaireData()
    upload_data.file_input.filename = None
    upload_data.file_input.value = open(
        os.path.join(script_dir(), "questionnaire.csv"), "rb"
    ).read()
    upload_data.file_input.filename = "questionnaire.csv"
    return upload_data.data


def init_scores():
    suggestQuestionnaires = SuggestQuestionnaireScores()
    suggestQuestionnaires.data = upload_questionnaire()
    suggestQuestionnaires.init_dict_scores()
    return suggestQuestionnaires.data, suggestQuestionnaires.dict_scores
