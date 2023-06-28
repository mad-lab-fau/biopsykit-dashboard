import pytest
from src.Physiological import physiological_pipeline


@pytest.fixture
def signal_type():
    return physiological_pipeline.PhysSignalType()


def test_constructor(signal_type):
    """Tests default values of PhysSignalType"""
    assert signal_type.ready == False
    assert signal_type.selected_signal == ""
    assert signal_type.options == ["", "ECG", "CFT", "RSP", "EEG"]


def test_signal_selected(signal_type):
    """Tests if the function signal_selected works correctly"""
    signal_type.selected_signal = "ECG"
    assert signal_type.selected_signal == "ECG"
    assert signal_type.ready == True
    signal_type.selected_signal = ""
    assert signal_type.selected_signal == ""
    assert signal_type.ready == False
    with pytest.raises(Exception):
        signal_type.selected_signal = "FalseSignal"
    assert signal_type.selected_signal != "FalseSignal"
