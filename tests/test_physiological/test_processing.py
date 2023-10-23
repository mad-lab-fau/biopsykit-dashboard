import os
from pathlib import Path
from typing import Tuple, Dict

import nilspodlib
import pandas as pd
import biopsykit as bp
import pytest
from biopsykit.io.eeg import MuseDataset
from nilspodlib import Dataset

from src.Physiological.add_times import AddTimes
from src.Physiological.processing_and_preview import ProcessingAndPreview


class TestProcessingAndPreview:
    @pytest.fixture
    def processing_and_preview(self):
        return ProcessingAndPreview()

    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    def test_ecg_processing(self, processing_and_preview, script_dir):
        processing_and_preview.signal = "ECG"
        processing_and_preview.signal = "ECG"
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
        processing_and_preview.data = {"ecg_sample_Vp01.bin": df}
        processing_and_preview.selected_outlier_methods = None
        processing_and_preview.outlier_params = None
        processing_and_preview.sampling_rate = fs
        try:
            processing_and_preview.processing()
        except Exception as e:
            assert False, e
        assert processing_and_preview.ecg_processor["ecg_sample_Vp01.bin"] is not None
        assert (
            processing_and_preview.ecg_processor["ecg_sample_Vp01.bin"].ecg_result
            is not None
        )
        df, fs = self.get_sample_ecg_data(script_dir, "Vp02")
        processing_and_preview.data["ecg_sample_Vp02.bin"] = df
        try:
            processing_and_preview.processing()
        except Exception as e:
            assert False, e
        assert processing_and_preview.ecg_processor["ecg_sample_Vp02.bin"] is not None
        assert (
            processing_and_preview.ecg_processor["ecg_sample_Vp02.bin"].ecg_result
            is not None
        )
        assert len(processing_and_preview.ecg_processor) == 2

    def test_ecg_processing_with_timelog(self, processing_and_preview, script_dir):
        add_times = AddTimes()
        add_times.df = pd.read_excel(os.path.join(script_dir, "ecg_time_log.xlsx"))
        add_times.df = add_times.handle_time_file(add_times.df)
        add_times.set_subject_time_dict()
        processing_and_preview.subject_time_dict = add_times.subject_time_dict
        processing_and_preview.signal = "ECG"
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
        processing_and_preview.data = {"Vp01": df}
        processing_and_preview.selected_outlier_methods = None
        processing_and_preview.outlier_params = None
        processing_and_preview.sampling_rate = fs
        try:
            processing_and_preview.processing()
        except Exception as e:
            assert False, e
        assert processing_and_preview.ecg_processor["Vp01"] is not None
        assert processing_and_preview.ecg_processor["Vp01"].ecg_result is not None
        assert processing_and_preview.ecg_processor["Vp01"].phases is not None
        assert len(processing_and_preview.ecg_processor["Vp01"].phases) == 4

    def test_eeg_processing(self, processing_and_preview, script_dir):
        processing_and_preview.signal = "EEG"
        (
            processing_and_preview.data,
            processing_and_preview.sampling_rate,
        ) = self.get_sample_eeg_data(script_dir)
        try:
            processing_and_preview.processing()
        except Exception as e:
            assert False, e
        assert "Vp01" in processing_and_preview.eeg_processor.keys()
        assert processing_and_preview.eeg_processor["Vp01"] is not None
        assert processing_and_preview.eeg_processor["Vp01"].eeg_result is not None
        assert (
            processing_and_preview.eeg_processor["Vp01"].eeg_result["Data"].shape[0]
            == 925
        )
        assert (
            processing_and_preview.eeg_processor["Vp01"].eeg_result["Data"].shape[1]
            == 4
        )

    def test_rsp_processing(self, processing_and_preview, script_dir):
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
        processing_and_preview.signal = "RSP"
        processing_and_preview.estimate_rsp = True
        processing_and_preview.sampling_rate = fs
        processing_and_preview.data = {"Vp01": df}
        try:
            processing_and_preview.processing()
        except Exception as e:
            assert False, e

    @staticmethod
    def get_sample_eeg_data(script_dir: str) -> Tuple[Dict[str, pd.DataFrame], float]:
        df = pd.read_csv(os.path.join(script_dir, "EEG.csv"))
        muse = MuseDataset(df, "Europe/Berlin")
        df = muse.data_as_df("local_datetime")
        return {"Vp01": df}, muse.sampling_rate_hz

    @staticmethod
    def get_sample_ecg_data(script_dir: str, person: str) -> Tuple[pd.DataFrame, float]:
        sensor_data, counter, session_header = nilspodlib.dataset.parse_binary(
            os.path.join(script_dir, f"ecg_sample_{person}.bin"), tz="Europe/Berlin"
        )
        ds = Dataset(sensor_data, counter, session_header)
        df, fs = bp.io.nilspod.load_dataset_nilspod(dataset=ds)
        return df, fs
