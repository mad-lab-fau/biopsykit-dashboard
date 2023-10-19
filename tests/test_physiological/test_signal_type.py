import pytest
from src.Physiological import physiological_pipeline


class TestSignalType:
    @pytest.fixture
    def signal_type(self):
        return physiological_pipeline.PhysSignalType()

    def test_constructor(self, signal_type):
        """Tests default values of PhysSignalType"""
        assert signal_type.ready == False
        assert signal_type.signal == ""
        assert signal_type.select_signal.options == ["", "ECG", "RSP", "EEG"]

    def test_signal_selected(self, signal_type):
        """Tests if the function signal_selected works correctly"""
        signal_type.select_signal.value = "ECG"
        assert signal_type.signal == "ECG"
        assert signal_type.ready == True
        signal_type.select_signal.value = ""
        assert signal_type.signal == ""
        assert signal_type.ready == False
        signal_type.select_signal.value = "FalseSignal"
        assert signal_type.signal != "FalseSignal"
        assert signal_type.ready == False
