import pytest

from src.Physiological.process_hrv import AskToProcessHRV, SetHRVParameters


class TestProcessHrv:
    @pytest.fixture
    def ask_to_process_hrv(self):
        return AskToProcessHRV()

    @pytest.fixture
    def set_hrv_parameters(self):
        return SetHRVParameters()

    def test_constructor(self, ask_to_process_hrv):
        assert ask_to_process_hrv.ready == False

    def test_btn_behavior(self, ask_to_process_hrv):
        ask_to_process_hrv.skip_btn.clicks += 1
        assert ask_to_process_hrv.next_page == "Now the Files will be processed"
        assert ask_to_process_hrv.ready == True
        ask_to_process_hrv.default_btn.clicks += 1
        assert ask_to_process_hrv.next_page == "Now the Files will be processed"
        assert ask_to_process_hrv.ready == True
        ask_to_process_hrv.expert_mode_btn.clicks += 1
        assert ask_to_process_hrv.next_page == "Set HRV Parameters"
        assert ask_to_process_hrv.ready == True

    def test_set_hrv_parameter_change_values(self, set_hrv_parameters):
        set_hrv_parameters.set_hrv_index_name.value = "Test"
        assert set_hrv_parameters.hrv_index_name == "Test"
        set_hrv_parameters.check_correct_rpeaks.value = False
        assert set_hrv_parameters.correct_rpeaks == False
        set_hrv_parameters.select_hrv_types.value = ["hrv_time"]
        assert set_hrv_parameters.hrv_types == ["hrv_time"]
        set_hrv_parameters.select_hrv_types.value = ["hrv_nonlinear"]
        assert set_hrv_parameters.hrv_types == ["hrv_nonlinear"]
        set_hrv_parameters.select_hrv_types.value = ["hrv_time", "hrv_nonlinear"]
        assert set_hrv_parameters.hrv_types == ["hrv_time", "hrv_nonlinear"]
