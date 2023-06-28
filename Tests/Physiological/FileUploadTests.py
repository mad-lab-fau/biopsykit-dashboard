import pandas as pd
import pytest
import os

from biopsykit.io.eeg import MuseDataset

from src.Physiological.file_upload import FileUpload


@pytest.fixture
def file_upload():
    return FileUpload()


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


def test_constructor(file_upload):
    """Tests default values of FileUpload"""
    assert file_upload.ready == True
    assert file_upload.selected_signal == ""
    assert file_upload.next == "Data arrived"


def test_changing_timezone(file_upload):
    file_upload.timezone = "Europe/Berlin"
    assert file_upload.timezone == "Europe/Berlin"
    assert file_upload.ready == True
    file_upload.timezone = "None Selected"
    assert file_upload.timezone == "None Selected"
    assert file_upload.ready == False


def test_change_selected_hardware(file_upload):
    file_upload.hardware = "BioPac"
    assert file_upload.hardware == "BioPac"
    assert file_upload.file_input.accept == ".acq"
    file_upload.hardware = "NilsPod"
    assert file_upload.file_input.accept == ".csv,.bin, .zip"
    with pytest.raises(Exception):
        file_upload.hardware = "False Hardware"


def test_extract_simple_zip(file_upload, script_dir):
    file_name = "Archiv.zip"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_zip_file(f.read())
    assert file_upload.file_input.filename == "Archiv.zip"
    assert_extracted_files(file_upload)


def test_extract_directory_structure(file_upload, script_dir):
    file_name = "Archiv_OrdnerStruktur.zip"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_zip_file(f.read())
    assert file_upload.file_input.filename == "Archiv_OrdnerStruktur.zip"
    assert_extracted_files(file_upload)


def test_extract_mixed_structure(file_upload, script_dir):
    file_name = "Archiv_Mischstruktur.zip"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_zip_file(f.read())
    assert file_upload.file_input.filename == "Archiv_Mischstruktur.zip"
    assert_extracted_files(file_upload)


def assert_extracted_files(file_upload):
    assert file_upload.ready == True
    assert file_upload.sampling_rate == 256.0
    assert isinstance(file_upload.data, dict)
    assert len(file_upload.data) == 2
    assert file_upload.data.keys() == {"Vp01", "Vp02"}
    assert file_upload.data["Vp01"].shape == (157790, 7)
    assert file_upload.data["Vp02"].shape == (120626, 7)


def test_handle_csv_file(file_upload, script_dir):
    file_name = "ECG.csv"
    abs_file_path = os.path.join(script_dir, file_name)
    file_upload.selected_signal = "ECG"
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_csv_file(f.read())
    assert file_upload.file_input.filename == "ECG.csv"
    assert file_upload.ready == True
    assert isinstance(file_upload.data, pd.DataFrame)
    file_name = "EEG.csv"
    abs_file_path = os.path.join(script_dir, file_name)
    file_upload.selected_signal = "EEG"
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_csv_file(f.read())
    assert file_upload.file_input.filename == "EEG.csv"
    assert file_upload.ready == True
    assert isinstance(file_upload.data, MuseDataset)
    with pytest.raises(Exception):
        file_upload.handle_csv_file(None)


def test_handle_bin_file(file_upload, script_dir):
    file_name = "ecg_sample_Vp01.bin"
    abs_file_path = os.path.join(script_dir, file_name)
    with open(abs_file_path, "rb") as f:
        file_upload.file_input.filename = file_name
        file_upload.handle_bin_file(f.read())
    assert file_upload.file_input.filename == "ecg_sample_Vp01.bin"
    assert file_upload.ready == True
    assert isinstance(file_upload.data, pd.DataFrame)
    assert file_upload.data.shape == (157790, 7)
    assert file_upload.sampling_rate == 256.0
