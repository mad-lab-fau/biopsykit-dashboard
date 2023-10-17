import os

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


def init_scores():
    suggestQuestionnaires = SuggestQuestionnaireScores()
    suggestQuestionnaires.data = upload_questionnaire()
    suggestQuestionnaires.init_dict_scores()
    return suggestQuestionnaires.data, suggestQuestionnaires.dict_scores
