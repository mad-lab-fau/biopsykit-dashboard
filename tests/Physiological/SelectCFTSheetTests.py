import os

import pytest

from src.Physiological.file_upload import FileUpload
from src.Physiological.select_cft_sheet import SelectCFTSheet


@pytest.fixture
def select_cft_sheet():
    return SelectCFTSheet()


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


@pytest.fixture
def select_cft_sheet_with_data(script_dir):
    file_upload = FileUpload()
    file_upload.select_hardware.value = "NilsPod"
    file_upload.select_timezone.value = "Europe/Berlin"
    file_name = "ecg_sample_Vp01.bin"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_bin_file(file_name, f.read())
    select_cft_sheet_with_data = SelectCFTSheet()
    select_cft_sheet_with_data.data = file_upload.data
    select_cft_sheet_with_data.sampling_rate = file_upload.sampling_rate
    return select_cft_sheet_with_data


def test_constructor(select_cft_sheet):
    assert select_cft_sheet.ready == False
    assert select_cft_sheet.select_cft_sheets.value == []
    assert select_cft_sheet.select_cft_sheets.options == []


def test_check_sheets(select_cft_sheet_with_data):
    select_cft_sheet_with_data.panel()
    assert select_cft_sheet_with_data.select_cft_sheets.options == [
        "ecg_sample_Vp01.bin",
    ]
    select_cft_sheet_with_data.select_cft_sheets.value = [
        "ecg_sample_Vp01.bin",
    ]
    assert select_cft_sheet_with_data.ready == True
