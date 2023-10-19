import pytest

from src.Questionnaire.loading_parameters import (
    AskToSetLoadingParameters,
    SetLoadingParametersManually,
)


class TestLoadingParameters:
    @pytest.fixture
    def ask_to_set_loading_parameters(self):
        return AskToSetLoadingParameters()

    @pytest.fixture
    def set_loading_parameters(self):
        return SetLoadingParametersManually()

    def test_ask_to_set_loading_parameters(self, ask_to_set_loading_parameters):
        assert ask_to_set_loading_parameters is not None
        assert ask_to_set_loading_parameters.next == "Upload Questionnaire Data"
        assert ask_to_set_loading_parameters.ready is False

    def test_clicking_buttons(self, ask_to_set_loading_parameters):
        ask_to_set_loading_parameters.default_btn.clicks += 1
        assert ask_to_set_loading_parameters.next == "Upload Questionnaire Data"
        assert ask_to_set_loading_parameters.ready is True
        ask_to_set_loading_parameters.set_parameters_manually.clicks += 1
        assert ask_to_set_loading_parameters.next == "Set Loading Parameters"
        assert ask_to_set_loading_parameters.ready is True

    def test_setting_loading_parameters_manually(self, set_loading_parameters):
        assert set_loading_parameters.select_subject_col.value is None
        assert set_loading_parameters.set_condition_col.value is None
        assert set_loading_parameters.set_additional_index_cols.value is None
        set_loading_parameters.select_subject_col.value = "subject"
        set_loading_parameters.set_condition_col.value = "condition"
        set_loading_parameters.set_additional_index_cols.value = ["index1", "index2"]
        set_loading_parameters.check_replace_missing_vals.value = False
        set_loading_parameters.check_remove_nan_rows.value = False
        set_loading_parameters.set_sheet_name.value = "sheet_name"
        assert set_loading_parameters.subject_col == "subject"
        assert set_loading_parameters.condition_col == "condition"
        assert set_loading_parameters.additional_index_cols == [
            "index1",
            "index2",
        ]
        assert set_loading_parameters.replace_missing_vals is False
        assert set_loading_parameters.remove_nan_rows is False
