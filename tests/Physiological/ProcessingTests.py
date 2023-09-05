from typing import Tuple, Dict

import nilspodlib
import pandas as pd
import biopsykit as bp
from biopsykit.io.eeg import MuseDataset
from nilspodlib import Dataset

from src.Physiological.add_times import AddTimes
from src.Physiological.processing_and_preview import ProcessingAndPreview


def test_ecg_processing():
    process = ProcessingAndPreview()
    process.selected_signal = "ECG"
    process.selected_signal = "ECG"
    df, fs = get_sample_ecg_data("Vp01")
    process.data = {"ecg_sample_Vp01.bin": df}
    process.selected_outlier_methods = None
    process.outlier_params = None
    process.sampling_rate = fs
    try:
        process.processing()
    except Exception as e:
        assert False, e
    assert process.ecg_processor["ecg_sample_Vp01.bin"] is not None
    assert process.ecg_processor["ecg_sample_Vp01.bin"].ecg_result is not None
    df, fs = get_sample_ecg_data("Vp02")
    process.data["ecg_sample_Vp02.bin"] = df
    try:
        process.processing()
    except Exception as e:
        assert False, e
    assert process.ecg_processor["ecg_sample_Vp02.bin"] is not None
    assert process.ecg_processor["ecg_sample_Vp02.bin"].ecg_result is not None
    assert len(process.ecg_processor) == 2


def test_ecg_processing_with_timelog():
    process = ProcessingAndPreview()
    add_times = AddTimes()
    add_times.df = pd.read_excel("./example_data/ecg_time_log.xlsx")
    add_times.df = add_times.handle_time_file(add_times.df)
    add_times.set_subject_time_dict()
    process.subject_time_dict = add_times.subject_time_dict
    process.selected_signal = "ECG"
    df, fs = get_sample_ecg_data("Vp01")
    process.data = {"Vp01": df}
    process.selected_outlier_methods = None
    process.outlier_params = None
    process.sampling_rate = fs
    try:
        process.processing()
    except Exception as e:
        assert False, e
    assert process.ecg_processor["Vp01"] is not None
    assert process.ecg_processor["Vp01"].ecg_result is not None
    assert process.ecg_processor["Vp01"].phases is not None
    assert len(process.ecg_processor["Vp01"].phases) == 4


def test_eeg_processing():
    process = ProcessingAndPreview()
    process.selected_signal = "EEG"
    process.data, process.sampling_rate = get_sample_eeg_data()
    try:
        process.processing()
    except Exception as e:
        assert False, e
    assert process.eeg_processor["Vp01"] is not None
    assert process.eeg_processor["Vp01"].eeg_result is not None


def get_sample_eeg_data() -> Tuple[Dict[str, pd.DataFrame], float]:
    df = pd.read_csv(f"./example_data/EEG.csv")
    muse = MuseDataset(df, "Europe/Berlin")
    df = muse.data_as_df("local_datetime")
    return {"Vp01": df}, muse.sampling_rate_hz


def get_sample_ecg_data(person: str) -> Tuple[pd.DataFrame, float]:
    sensor_data, counter, session_header = nilspodlib.dataset.parse_binary(
        f"./example_data/ecg_sample_{person}.bin", tz="Europe/Berlin"
    )
    ds = Dataset(sensor_data, counter, session_header)
    df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=ds)
    return df, fs
