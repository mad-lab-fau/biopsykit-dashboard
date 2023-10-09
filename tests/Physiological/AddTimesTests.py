import os

import pytest

from src.Physiological.add_times import AskToAddTimes, AddTimes


@pytest.fixture
def ask_to_add_times():
    return AskToAddTimes()


@pytest.fixture
def add_times():
    return AddTimes()


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


def test_ask_to_add_times_constructor(ask_to_add_times):
    assert ask_to_add_times.next == "Add Times"
    assert ask_to_add_times.ready == False


def test_skip_btn(ask_to_add_times):
    ask_to_add_times.skip_btn.clicks = 1
    assert ask_to_add_times.ready == True
    assert ask_to_add_times.next == "Do you want to detect Outlier?"
    ask_to_add_times.signal = "EEG"
    ask_to_add_times.skip_btn.clicks = 2
    assert ask_to_add_times.ready == True
    assert ask_to_add_times.next == "Frequency Bands"


def test_add_times_btn(ask_to_add_times):
    ask_to_add_times.add_times_btn.clicks = 1
    assert ask_to_add_times.ready == True
    assert ask_to_add_times.next == "Add Times"
    ask_to_add_times.signal = "EEG"
    ask_to_add_times.add_times_btn.clicks = 2
    assert ask_to_add_times.ready == True
    assert ask_to_add_times.next == "Add Times"


def test_upload_perfect_file(add_times, script_dir):
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


def test_upload_subject_time_file_missing_subject(add_times, script_dir):
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


def test_upload_subject_time_file_all_missing(add_times, script_dir):
    file_name = "ecg_time_log_changed_all.xlsx"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        add_times.time_upload.filename = file_name
        add_times.time_upload.value = f.read()
    assert add_times.ready == False
    add_times.select_subject.value = "versuchspersonen"
    assert add_times.ready == False
    add_times.select_condition.value = "cas"
    assert add_times.ready == True
    keys = ["Vp01", "Vp02"]
    for key in keys:
        assert key in add_times.subject_time_dict.keys()
