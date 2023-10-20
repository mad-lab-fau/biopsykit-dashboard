import os
from pathlib import Path
from typing import Tuple, Dict

import nilspodlib
import pandas as pd
import biopsykit as bp
import pytest
from biopsykit.io.eeg import MuseDataset
from nilspodlib import Dataset

from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.add_times import AddTimes
from src.Physiological.processing_and_preview import ProcessingAndPreview


class TestProcessingAndPreview:
    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    def test_ecg_processing(self, script_dir):
        process = ProcessingAndPreview()
        process.signal = "ECG"
        process.signal = "ECG"
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
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
        df, fs = self.get_sample_ecg_data(script_dir, "Vp02")
        process.data["ecg_sample_Vp02.bin"] = df
        try:
            process.processing()
        except Exception as e:
            assert False, e
        assert process.ecg_processor["ecg_sample_Vp02.bin"] is not None
        assert process.ecg_processor["ecg_sample_Vp02.bin"].ecg_result is not None
        assert len(process.ecg_processor) == 2

    def test_ecg_processing_with_timelog(self, script_dir):
        process = ProcessingAndPreview()
        add_times = AddTimes()
        add_times.df = pd.read_excel(os.path.join(script_dir, "ecg_time_log.xlsx"))
        add_times.df = add_times.handle_time_file(add_times.df)
        add_times.set_subject_time_dict()
        process.subject_time_dict = add_times.subject_time_dict
        process.signal = "ECG"
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
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

    def test_eeg_processing(self, script_dir):
        process = ProcessingAndPreview()
        process.signal = "EEG"
        process.data, process.sampling_rate = self.get_sample_eeg_data(script_dir)
        try:
            process.processing()
        except Exception as e:
            assert False, e
        assert "Vp01" in process.eeg_processor.keys()
        assert process.eeg_processor["Vp01"] is not None
        assert process.eeg_processor["Vp01"].eeg_result is not None
        assert process.eeg_processor["Vp01"].eeg_result["Data"].shape[0] == 925
        assert process.eeg_processor["Vp01"].eeg_result["Data"].shape[1] == 4

    def test_rsp_processing(self, script_dir):
        df, fs = self.get_sample_ecg_data(script_dir, "Vp01")
        process = ProcessingAndPreview()
        process.signal = "RSP"
        process.estimate_rsp = True
        process.sampling_rate = fs
        process.data = {"Vp01": df}
        try:
            process.processing()
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
