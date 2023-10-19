import pytest
import panel as pn
import biopsykit as bp

from src.Questionnaire.convert_scale import AskToConvertScales, ConvertScales
from tests.test_questionnaire.QuestionnaireBaseMethodsForTesting import init_scores


class TestConvertScales:
    @pytest.fixture
    def ask_to_convert_scales(self):
        return AskToConvertScales()

    @pytest.fixture
    def convert_scales(self):
        convert_scales = ConvertScales()
        convert_scales.data, convert_scales.dict_scores = init_scores()
        convert_scales.data_scaled = convert_scales.data.copy()
        return convert_scales

    @pytest.fixture
    def questionnaire_selector(self):
        return pn.widgets.Select(name="Select Questionnaire")

    @pytest.fixture
    def input_offset(self):
        return pn.widgets.IntInput(
            name="Offset",
            placeholder="Enter an offset for the selected columns",
            value=None,
        )

    @pytest.fixture
    def column_selector(self):
        return pn.widgets.CrossSelector(
            name="Columns to invert the data",
            options=["PANAS_01_Pre", "PANAS_02_Pre"],
        )

    def test_ask_to_convert_scales_constructor(self, ask_to_convert_scales):
        assert ask_to_convert_scales is not None
        assert ask_to_convert_scales.next_page == "Convert Scales"
        assert ask_to_convert_scales.ready is False

    def test_ask_to_convert_scales_btn_clicks(self, ask_to_convert_scales):
        assert ask_to_convert_scales is not None
        ask_to_convert_scales.convert_scales_btn.clicks += 1
        assert ask_to_convert_scales.next_page == "Convert Scales"
        assert ask_to_convert_scales.ready is True
        ask_to_convert_scales.skip_converting_btn.clicks += 1
        assert ask_to_convert_scales.next_page == "Ask To crop scales"
        assert ask_to_convert_scales.ready is True

    def test_convert_scales_constructor(self, convert_scales):
        assert convert_scales is not None
        assert convert_scales.change_questionnaires_btn is not None
        assert convert_scales.change_columns_btn is not None
        assert convert_scales.change_columns_col is not None
        assert convert_scales.questionnaire_col is not None

    def test_apply_questionnaire_scale_change(
        self, convert_scales, questionnaire_selector, input_offset
    ):
        assert convert_scales is not None
        assert convert_scales.data is not None
        convert_scales.change_questionnaires_btn.clicks += 1
        assert convert_scales.questionnaire_col.visible is True
        assert convert_scales.change_columns_col.visible is False
        data_before = convert_scales.data
        questionnaire_selector.value = "Not a valid questionnaire"
        input_offset.value = 0
        convert_scales.apply_questionnaire_scale(
            (questionnaire_selector, input_offset), None
        )
        assert convert_scales.data is not None
        assert convert_scales.data.equals(data_before) is True
        questionnaire_selector.value = "panas-pre"
        input_offset.value = 1
        convert_scales.apply_questionnaire_scale(
            (questionnaire_selector, input_offset), None
        )
        assert convert_scales.data is not None
        assert convert_scales.data_scaled.equals(convert_scales.data) is False

    def test_apply_column_scale(self, convert_scales, column_selector, input_offset):
        assert convert_scales is not None
        assert convert_scales.data_scaled is not None
        convert_scales.change_columns_btn.clicks += 1
        assert convert_scales.change_columns_col.visible is True
        assert convert_scales.questionnaire_col.visible is False
        data_before = convert_scales.data_scaled.copy()
        column_selector.value = []
        input_offset.value = 300
        convert_scales.apply_column_scale((column_selector, input_offset), None)
        assert convert_scales.data_scaled is not None
        assert convert_scales.data_scaled.equals(data_before) is True
        column_selector.value = ["PANAS_01_Pre", "PANAS_02_Pre"]
        input_offset.value = 20
        convert_scales.apply_column_scale((column_selector, input_offset), None)
        assert convert_scales.data_scaled is not None
        assert convert_scales.data_scaled.equals(data_before) is False
        correctly_scaled = bp.questionnaires.utils.convert_scale(
            data_before, cols=["PANAS_01_Pre", "PANAS_02_Pre"], offset=20
        )
        assert convert_scales.data_scaled.equals(correctly_scaled) is True
