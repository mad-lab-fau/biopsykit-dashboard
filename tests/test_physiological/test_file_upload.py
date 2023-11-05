from pathlib import Path

import pytest
import os


from src.Physiological.file_upload import FileUpload


class TestFileUpload:
    @pytest.fixture
    def file_upload(self):
        return FileUpload()

    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    def test_constructor(self, file_upload):
        """Tests default values of FileUpload"""
        assert file_upload.ready == False
        assert file_upload.timezone == "Europe/Berlin"
        assert file_upload.file_input.accept == ".csv,.bin,.xlsx"
        assert file_upload.file_input.multiple == False

    def test_changing_timezone(self, file_upload):
        file_upload.select_timezone.value = "None Selected"
        assert file_upload.timezone == "None Selected"
        assert file_upload.ready == False
        file_upload.select_timezone.value = "Europe/Berlin"
        assert file_upload.timezone == "Europe/Berlin"
        assert file_upload.ready == True

    def test_change_selected_hardware(self, file_upload):
        file_upload.select_hardware.value = "BioPac"
        assert file_upload.hardware == "BioPac"
        assert file_upload.file_input.accept == ".acq"
        file_upload.select_hardware.value = "NilsPod"
        assert file_upload.file_input.accept == ".csv,.bin, .zip"
        with pytest.raises(Exception):
            file_upload.select_hardware.value = "False Hardware"

    def test_extract_simple_zip(self, file_upload, script_dir):
        file_name = "Archiv.zip"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_zip_file(f.read())
        assert file_upload.file_input.filename == "Archiv.zip"
        self.assert_extracted_files(file_upload)

    def test_extract_directory_structure(self, file_upload, script_dir):
        file_name = "Archiv_OrdnerStruktur.zip"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_zip_file(f.read())
        assert file_upload.file_input.filename == "Archiv_OrdnerStruktur.zip"
        self.assert_extracted_files(file_upload)

    def test_extract_mixed_structure(self, file_upload, script_dir):
        file_name = "Archiv_Mischstruktur.zip"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_zip_file(f.read())
        assert file_upload.file_input.filename == "Archiv_Mischstruktur.zip"
        self.assert_extracted_files(file_upload)

    def test_multiple_subjects_multiple_sessions(self, file_upload, script_dir):
        file_name = "Archiv_OrdnerStrukturMultipleSessions.zip"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_zip_file(f.read())
        assert file_upload.file_input.filename == file_name
        assert file_upload.ready == True
        assert file_upload.sampling_rate == 256.0
        assert isinstance(file_upload.data, dict)
        assert len(file_upload.data) == 2
        assert file_upload.data.keys() == {"Vp01", "Vp02"}

    def assert_extracted_files(self, file_upload):
        assert file_upload.ready == True
        assert file_upload.sampling_rate == 256.0
        assert isinstance(file_upload.data, dict)
        assert len(file_upload.data) == 2
        assert file_upload.data.keys() == {"Vp01", "Vp02"}
        assert file_upload.data["Vp01"].shape == (157790, 7)
        assert file_upload.data["Vp02"].shape == (120626, 7)

    def test_handle_csv_file(self, file_upload, script_dir):
        file_name = "ECG.csv"
        abs_file_path = os.path.join(script_dir, file_name)
        file_upload.signal = "ECG"
        file_upload.file_input.value = open(abs_file_path, "rb").read()
        file_upload.file_input.filename = file_name
        assert file_upload.file_input.filename == "ECG.csv"
        assert file_upload.ready == True
        assert isinstance(file_upload.data, dict)
        file_name = "EEG.csv"
        abs_file_path = os.path.join(script_dir, file_name)
        file_upload.signal = "EEG"
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_csv_file(file_name, f.read())
        assert file_upload.file_input.filename == "EEG.csv"
        assert file_upload.ready == True
        assert isinstance(file_upload.data, dict)
        with pytest.raises(Exception):
            file_upload.handle_csv_file(file_name, None)

    def test_handle_bin_file(self, file_upload, script_dir):
        file_name = "ecg_sample_Vp01.bin"
        abs_file_path = os.path.join(script_dir, file_name)
        with open(abs_file_path, "rb") as f:
            file_upload.file_input.filename = file_name
            file_upload.handle_bin_file(file_name, f.read())
        assert file_upload.file_input.filename == "ecg_sample_Vp01.bin"
        assert file_upload.ready == True
        assert isinstance(file_upload.data, dict)
        assert file_upload.data[file_name].shape == (157790, 7)
        assert file_upload.sampling_rate == 256.0
