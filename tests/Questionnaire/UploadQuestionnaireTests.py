import os

import pytest

from src.Questionnaire.upload_questionnaire_data import UploadQuestionnaireData


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


@pytest.fixture
def questionnaire_filename_csv():
    return "questionnaire.csv"


@pytest.fixture
def questionnaire_filename_xlsx():
    return "questionnaire.xlsx"


@pytest.fixture
def upload_questionnaire():
    return UploadQuestionnaireData()


def test_constructor_upload_questionnaire(upload_questionnaire):
    assert upload_questionnaire is not None
    assert upload_questionnaire.ready is False
    assert upload_questionnaire.data is None


def test_upload_csv_file(upload_questionnaire, questionnaire_filename_csv):
    upload_questionnaire.file_input.filename = questionnaire_filename_csv
    with open(
        os.path.join(
            os.path.dirname(__file__), "example_data", questionnaire_filename_csv
        ),
        "rb",
    ) as f:
        upload_questionnaire.file_input.value = f.read()
    assert upload_questionnaire.ready is True
    assert upload_questionnaire.data is not None


def test_upload_xlsx_file(upload_questionnaire, questionnaire_filename_xlsx):
    upload_questionnaire.file_input.filename = questionnaire_filename_xlsx
    with open(
        os.path.join(
            os.path.dirname(__file__), "example_data", questionnaire_filename_xlsx
        ),
        "rb",
    ) as f:
        upload_questionnaire.file_input.value = f.read()
    assert upload_questionnaire.ready is True
    assert upload_questionnaire.data is not None


def test_upload_corrupted_csv_file(upload_questionnaire):
    upload_questionnaire.file_input.filename = "corrupted.csv"
    upload_questionnaire.file_input.value = b"corrupted"
    assert upload_questionnaire.ready is False
    assert upload_questionnaire.data is None
