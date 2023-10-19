import os
from pathlib import Path

import pytest
from pandas import Timestamp

from src.Physiological.data_arrived import DataArrived
from src.Physiological.file_upload import FileUpload


class TestDataArrived:
    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    @pytest.fixture
    def data_arrived(self):
        return DataArrived()

    @pytest.fixture
    def data_arrived_with_one_file(self, script_dir):
        file_upload = FileUpload()
        file_upload.select_hardware.value = "NilsPod"
        file_upload.select_timezone.value = "Europe/Berlin"
        file_name = "ecg_sample_Vp01.bin"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_bin_file(file_name, f.read())
        data_arrived = DataArrived()
        data_arrived.data = file_upload.data
        data_arrived.sampling_rate = file_upload.sampling_rate
        return data_arrived

    def test_constructor(self, data_arrived):
        assert data_arrived.ready == False
        assert data_arrived.next == "Do you want to add time logs?"
        assert data_arrived.sampling_rate == -1

    def test_set_sampling_rate_value(self, data_arrived):
        data_arrived.sampling_rate_input.value = "100"
        assert data_arrived.sampling_rate == 100.0
        assert data_arrived.ready == True
        data_arrived.sampling_rate_input.value = "100.0"
        assert data_arrived.sampling_rate == 100.0
        assert data_arrived.ready == True
        data_arrived.sampling_rate_input.value = "NaN"
        assert data_arrived.sampling_rate == -1.0
        assert data_arrived.ready == False
        data_arrived.sampling_rate_input.value = "Keine Zahl"
        assert data_arrived.sampling_rate == -1.0
        assert data_arrived.ready == False
        data_arrived.sampling_rate_input.value = "100K"
        assert data_arrived.sampling_rate == -1.0
        assert data_arrived.ready == False

    def test_change_subject(self, data_arrived_with_one_file):
        assert data_arrived_with_one_file.data is not None
        assert data_arrived_with_one_file.subject_selector.value is None
        assert data_arrived_with_one_file.session_start.visible == False
        assert data_arrived_with_one_file.session_end.visible == False
        assert data_arrived_with_one_file.data_view.visible == False
        data_arrived_with_one_file.subject_selector.value = "ecg_sample_Vp01.bin"
        assert (
            data_arrived_with_one_file.subject_selector.value == "ecg_sample_Vp01.bin"
        )
        assert data_arrived_with_one_file.session_start.visible == True
        assert data_arrived_with_one_file.session_end.visible == True
        assert data_arrived_with_one_file.data_view.visible == True
        start_timestamp = Timestamp(1571826711003906000, tz="Europe/Berlin")
        end_timestamp = Timestamp(1571827327367187000, tz="Europe/Berlin")
        assert data_arrived_with_one_file.session_start.value == start_timestamp
        assert data_arrived_with_one_file.session_end.value == end_timestamp
        data_arrived_with_one_file.subject_selector.value = ""
        assert data_arrived_with_one_file.subject_selector.value == ""
        assert data_arrived_with_one_file.session_start.visible == False
        assert data_arrived_with_one_file.session_end.visible == False
        assert data_arrived_with_one_file.data_view.visible == False
