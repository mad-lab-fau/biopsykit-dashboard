import os
from pathlib import Path

import pytest

from src.Questionnaire.upload_questionnaire_data import UploadQuestionnaireData


class TestUploadQuestionnaireData:
    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    @pytest.fixture
    def questionnaire_filename_csv(self):
        return "questionnaire.csv"

    @pytest.fixture
    def questionnaire_filename_xlsx(self):
        return "questionnaire.xlsx"

    @pytest.fixture
    def upload_questionnaire(self):
        upload_questionnaire = UploadQuestionnaireData()
        upload_questionnaire.file_input.value = None
        upload_questionnaire.file_input.filename = None
        return UploadQuestionnaireData()

    def test_constructor_upload_questionnaire(self, upload_questionnaire):
        assert upload_questionnaire is not None
        assert upload_questionnaire.ready is False
        assert upload_questionnaire.data is None

    def test_upload_csv_file(
        self, upload_questionnaire, questionnaire_filename_csv, script_dir
    ):
        with open(
            os.path.join(script_dir, questionnaire_filename_csv),
            "rb",
        ) as f:
            upload_questionnaire.file_input.value = f.read()
        upload_questionnaire.file_input.filename = questionnaire_filename_csv
        assert upload_questionnaire.data is not None
        assert upload_questionnaire.ready is True

    def test_upload_xlsx_file(
        self, upload_questionnaire, questionnaire_filename_xlsx, script_dir
    ):
        with open(
            os.path.join(script_dir, questionnaire_filename_xlsx),
            "rb",
        ) as f:
            upload_questionnaire.file_input.value = f.read()
        upload_questionnaire.file_input.filename = questionnaire_filename_xlsx
        assert upload_questionnaire.data is not None
        assert upload_questionnaire.ready is True

    def test_upload_corrupted_csv_file(self, upload_questionnaire):
        upload_questionnaire.file_input.value = b"corrupted"
        upload_questionnaire.file_input.filename = "corrupted.csv"
        assert upload_questionnaire.data is None
        assert upload_questionnaire.ready is False
