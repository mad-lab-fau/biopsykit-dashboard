import pytest

from src.Sleep.choose_device import ChooseRecordingDevice


@pytest.fixture
def choose_recording_device():
    return ChooseRecordingDevice()


def test_choose_recording_device_constructor(choose_recording_device):
    assert choose_recording_device.ready == False
    assert "Polysomnography" in choose_recording_device.device_selector.options
    assert "Withings" in choose_recording_device.device_selector.options


def test_choose_recording_device_device_changed(choose_recording_device):
    choose_recording_device.device_selector.value = "Polysomnography"
    assert choose_recording_device.selected_device == "Polysomnography"
    assert choose_recording_device.ready == True
    choose_recording_device.device_selector.value = ""
    assert choose_recording_device.selected_device == ""
    assert choose_recording_device.ready == False
