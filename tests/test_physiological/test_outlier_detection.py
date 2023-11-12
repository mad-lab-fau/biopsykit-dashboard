import pytest

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import OUTLIER_METHODS
from src.Physiological.outlier_detection import AskToDetectOutliers, OutlierDetection


class TestOutlierDetection:
    @pytest.fixture
    def ask_to_detect_outlier(self):
        return AskToDetectOutliers()

    @pytest.fixture
    def detect_outlier(self):
        return OutlierDetection()

    def test_constructor(self, ask_to_detect_outlier):
        assert ask_to_detect_outlier.next == "Do you want to process the HRV also?"
        assert ask_to_detect_outlier.ready == False

    def test_skip_btn(self, ask_to_detect_outlier):
        ask_to_detect_outlier.skip_btn.clicks = 1
        assert ask_to_detect_outlier.ready == True
        assert ask_to_detect_outlier.next == "Do you want to process the HRV also?"
        assert ask_to_detect_outlier.skip_outlier_detection == True

    def test_default_btn(self, ask_to_detect_outlier):
        ask_to_detect_outlier.default_btn.clicks = 1
        assert ask_to_detect_outlier.ready == True
        assert ask_to_detect_outlier.next == "Do you want to process the HRV also?"
        assert ask_to_detect_outlier.skip_outlier_detection == False
        outlier_params = ask_to_detect_outlier.get_outlier_params()
        assert outlier_params["correlation"] == 0.3
        assert outlier_params["artifact"] == 0
        assert outlier_params["quality"] == 0.4
        assert outlier_params["statistical_rr"] == 2.576
        assert outlier_params["statistical_rr_diff"] == 1.96
        assert outlier_params["physiological"] == (45, 200)

    def test_expert_mode_btn(self, ask_to_detect_outlier):
        ask_to_detect_outlier.expert_mode_btn.clicks = 1
        assert ask_to_detect_outlier.ready == True
        assert ask_to_detect_outlier.next == "Expert Outlier Detection"
        assert ask_to_detect_outlier.skip_outlier_detection == False

    def test_outlier_detection_constructor(self, detect_outlier):
        assert detect_outlier.select_outlier_methods.value == ["quality", "artifact"]
        assert detect_outlier.select_outlier_methods.options == OUTLIER_METHODS

    def test_setting_upper_and_lower_bound(self, detect_outlier):
        detect_outlier.set_physiological_upper.value = -100
        assert detect_outlier.physiological_upper == 0
        detect_outlier.set_physiological_lower.value = -1000
        assert detect_outlier.physiological_lower == 0
        detect_outlier.set_physiological_upper.value = 1000
        assert detect_outlier.physiological_upper == 1000
        detect_outlier.set_physiological_lower.value = 100
        assert detect_outlier.physiological_lower == 100
        detect_outlier.set_physiological_lower.value = 10000
        assert detect_outlier.physiological_lower == 1000
        assert detect_outlier.physiological_upper == 10000
        detect_outlier.set_physiological_lower.value = 80
        detect_outlier.set_physiological_upper.value = 120
        assert detect_outlier.physiological_lower == 80
        assert detect_outlier.physiological_upper == 120
        detect_outlier.set_physiological_upper.value = 40
        assert detect_outlier.physiological_upper == 80
        assert detect_outlier.physiological_lower == 40
