import os
from pathlib import Path

import pytest

from src.Physiological.add_times import AskToAddTimes, AddTimes


class TestAddTimes:
    @pytest.fixture
    def ask_to_add_times(self):
        return AskToAddTimes()

    @pytest.fixture
    def add_times(self):
        return AddTimes()

    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    def test_ask_to_add_times_constructor(self, ask_to_add_times):
        assert ask_to_add_times.next == "Add Times"
        assert ask_to_add_times.ready == False

    def test_skip_btn(self, ask_to_add_times):
        ask_to_add_times.skip_btn.clicks = 1
        assert ask_to_add_times.ready == True
        assert ask_to_add_times.next == "Do you want to detect Outlier?"
        ask_to_add_times.signal = "EEG"
        ask_to_add_times.skip_btn.clicks = 2
        assert ask_to_add_times.ready == True
        assert ask_to_add_times.next == "Frequency Bands"

    def test_add_times_btn(self, ask_to_add_times):
        ask_to_add_times.add_times_btn.clicks = 1
        assert ask_to_add_times.ready == True
        assert ask_to_add_times.next == "Add Times"
        ask_to_add_times.signal = "EEG"
        ask_to_add_times.add_times_btn.clicks = 2
        assert ask_to_add_times.ready == True
        assert ask_to_add_times.next == "Add Times"

    def test_upload_subject_time_file_all_missing(self, add_times, script_dir):
        file_name = "ecg_time_log_changed_all.xlsx"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            add_times.time_upload.filename = file_name
            add_times.time_upload.value = f.read()
        assert add_times.ready == False
        add_times.select_subject.value = "versuchspersonen"
        assert "subject" in add_times.df.columns.to_list()
        assert add_times.ready == False
        add_times.select_condition.value = "cas"
        assert add_times.ready == True
        keys = ["Vp01", "Vp02"]
        for key in keys:
            assert key in add_times.subject_time_dict.keys()

    def test_upload_subject_time_file_missing_subject(self, add_times, script_dir):
        file_name = "ecg_time_log_changed.xlsx"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            add_times.time_upload.filename = file_name
            add_times.time_upload.value = f.read()
        assert add_times.ready == False
        add_times.select_subject.value = "versuchspersonen"
        assert add_times.ready == True
        keys = ["Vp01", "Vp02"]
        for key in keys:
            assert key in add_times.subject_time_dict.keys()

    def test_upload_perfect_file(self, add_times, script_dir):
        file_name = "ecg_time_log.xlsx"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            add_times.time_upload.filename = file_name
            add_times.time_upload.value = f.read()
        assert add_times.ready == True
        assert add_times.next == "Do you want to detect Outlier?"
        keys = ["Vp01", "Vp02"]
        for key in keys:
            assert key in add_times.subject_time_dict.keys()
