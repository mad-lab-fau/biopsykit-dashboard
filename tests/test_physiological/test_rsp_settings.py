import pytest

from src.Physiological.rsp_settings import SetRspParameters


class TestRspSettings:
    @pytest.fixture
    def set_rsp_settings(self):
        return SetRspParameters()

    def test_constructor(self, set_rsp_settings):
        assert set_rsp_settings.estimate_rsp == False
        assert set_rsp_settings.checkbox_estimate_rsp.value == False
        assert set_rsp_settings.estimate_rsp_method == "peak_trough_mean"

    def test_set_estimate_rsp(self, set_rsp_settings):
        set_rsp_settings.checkbox_estimate_rsp.value = True
        assert set_rsp_settings.estimate_rsp == True
        assert set_rsp_settings.select_estimation_method.visible == True
        assert set_rsp_settings.estimate_rsp_method is not None
        set_rsp_settings.checkbox_estimate_rsp.value = False
        assert set_rsp_settings.estimate_rsp == False
        set_rsp_settings.checkbox_estimate_rsp.value = True
        assert set_rsp_settings.estimate_rsp == True
        assert set_rsp_settings.select_estimation_method.visible == True
        assert set_rsp_settings.estimate_rsp_method is not None
        set_rsp_settings.estimate_rsp_method = "peak_trough_diff"
        assert set_rsp_settings.estimate_rsp_method == "peak_trough_diff"
