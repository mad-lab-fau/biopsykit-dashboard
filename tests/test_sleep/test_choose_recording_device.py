import pytest

from src.Sleep.choose_device import ChooseRecordingDevice


class TestChooseRecordingDevice:
    @pytest.fixture
    def choose_recording_device(self):
        return ChooseRecordingDevice()

    def test_choose_recording_device_constructor(self, choose_recording_device):
        assert choose_recording_device.ready == False
        assert "Polysomnography" in choose_recording_device.device_selector.options
        assert "Withings" in choose_recording_device.device_selector.options

    def test_choose_recording_device_device_changed(self, choose_recording_device):
        choose_recording_device.device_selector.value = "Polysomnography"
        assert choose_recording_device.selected_device == "Polysomnography"
        assert choose_recording_device.ready == True
        choose_recording_device.device_selector.value = ""
        assert choose_recording_device.selected_device == ""
        assert choose_recording_device.ready == False
