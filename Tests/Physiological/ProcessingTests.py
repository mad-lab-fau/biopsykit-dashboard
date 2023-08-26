import nilspodlib
import pytest
import biopsykit as bp
from nilspodlib import Dataset

from src.Physiological.processing_and_preview import (
    ProcessingPreStep,
    ProcessingAndPreview,
)


@pytest.fixture
def processing():
    return ProcessingAndPreview()


def test_ecg_processing():
    process = ProcessingAndPreview()
    process.selected_signal = "ECG"
    sensor_data, counter, session_header = nilspodlib.dataset.parse_binary(
        "./example_data/ecg_sample_Vp01.bin", tz="Europe/Berlin"
    )
    ds = Dataset(sensor_data, counter, session_header)
    df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=ds)
    process.data = {"ecg_sample_Vp01.bin": df}
    process.sampling_rate = fs
    try:
        process.processing()
    except Exception as e:
        assert False, e
