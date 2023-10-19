import pytest
import biopsykit as bp

from src.Questionnaire.crop_scale import AskToCropScale, CropScales
from tests.test_questionnaire.QuestionnaireBaseMethodsForTesting import init_scores


class TestCropScales:
    @pytest.fixture
    def ask_to_crop_scale(self):
        ask_to_crop_scale = AskToCropScale()
        return ask_to_crop_scale

    @pytest.fixture
    def crop_scales(self):
        crop_scales = CropScales()
        crop_scales.data, crop_scales.dict_scores = init_scores()
        crop_scales.data_scaled = crop_scales.data.copy()
        return crop_scales

    def test_ask_to_crop_scale_constructor(self, ask_to_crop_scale):
        assert ask_to_crop_scale is not None
        assert ask_to_crop_scale.next_page == "Crop Scales"
        assert ask_to_crop_scale.ready is False

    def test_ask_to_crop_scales_btn(self, ask_to_crop_scale):
        ask_to_crop_scale.crop_btn.clicks += 1
        assert ask_to_crop_scale.next_page == "Crop Scales"
        assert ask_to_crop_scale.ready is True
        ask_to_crop_scale.skip_btn.clicks += 1
        assert ask_to_crop_scale.next_page == "Ask to invert scores"
        assert ask_to_crop_scale.ready is True

    def test_crop_scales_constructor(self, crop_scales):
        assert crop_scales is not None
        assert crop_scales.crop_btn is not None
        assert crop_scales.questionnaire_selector is not None
        assert crop_scales.set_nan_checkbox is not None
        assert crop_scales.questionnaire_stat_values_df is not None
        assert crop_scales.score_range_arrayInput is not None

    def test_crop_data(self, crop_scales):
        assert crop_scales.data is not None
        data_before = crop_scales.data_scaled.copy()
        crop_scales.questionnaire_selector.value = None
        crop_scales.crop_btn.clicks += 1
        assert crop_scales.data_scaled.equals(data_before) is True
        crop_scales.questionnaire_selector.value = "panas-pre"
        crop_scales.crop_btn.clicks += 1
        assert crop_scales.data_scaled.equals(data_before) is True
        crop_scales.questionnaire_selector.value = "panas-pre"
        crop_scales.score_range_arrayInput.value = [1, 2]
        crop_scales.crop_btn.clicks += 1
        assert crop_scales.data_scaled.equals(data_before) is False
        data_cropped = data_before.copy()
        cols = crop_scales.dict_scores["panas-pre"]
        data_cropped[
            crop_scales.dict_scores["panas-pre"]
        ] = bp.questionnaires.utils.crop_scale(
            data=data_before[cols],
            score_range=[1, 2],
        )
        assert crop_scales.data_scaled.equals(data_cropped) is True
