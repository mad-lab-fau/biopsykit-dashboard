import os
import biopsykit as bp
import pytest

from src.Sleep.upload_sleep_data import UploadSleepData


@pytest.fixture
def upload_sleep_data():
    return UploadSleepData()


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


@pytest.fixture
def imu_bin_file_example_path():
    return "sleep_imu_sample_01.bin"


@pytest.fixture
def withings_csv_file_example_path():
    return "sleep.csv"


def test_upload_sleep_data_constructor(upload_sleep_data):
    assert upload_sleep_data.fs == None
    assert upload_sleep_data.ready == False
    assert upload_sleep_data.accepted_file_types == {
        "Polysomnography": ".edf, .zip",
        "Other IMU Device": ".bin, .zip",
        "Withings": ".csv, .zip",
    }
    assert upload_sleep_data.upload_data.name == "Upload sleep data"
    assert upload_sleep_data.upload_data.multiple == False
    assert upload_sleep_data.next_page == "Process Data"


def test_upload_sleep_data_process_imu_bin_file(
    upload_sleep_data, script_dir, imu_bin_file_example_path
):
    upload_sleep_data.selected_device = "Other IMU Device"
    upload_sleep_data.selected_parameters[upload_sleep_data.selected_device][
        "tz"
    ] = "Europe/Berlin"
    upload_sleep_data.upload_data.filename = imu_bin_file_example_path
    upload_sleep_data.upload_data.value = open(
        os.path.join(script_dir, imu_bin_file_example_path), "rb"
    ).read()
    assert upload_sleep_data.ready == True
    assert upload_sleep_data.next_page == "Process Data"
    data, _ = bp.example_data.get_sleep_imu_example()
    assert upload_sleep_data.data[imu_bin_file_example_path].equals(data)
