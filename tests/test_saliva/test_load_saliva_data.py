import os
from pathlib import Path

import pytest

from src.Saliva.load_saliva_data import LoadSalivaData


class TestLoadSalivaData:
    @pytest.fixture
    def load_saliva_data(self):
        return LoadSalivaData()

    @pytest.fixture
    def script_dir(self):
        full_path = os.path.dirname(__file__)
        directory = str(Path(full_path).parents[0])
        return os.path.join(directory, "test_data")

    @pytest.fixture
    def saliva_plate_file_name(self):
        return "cortisol_sample_plate.xlsx"

    def test_constructor_load_saliva_data(self, load_saliva_data):
        assert load_saliva_data.ready == False
        assert load_saliva_data.temporary_dataframe is None
        assert load_saliva_data.data is None
        assert load_saliva_data.saliva_type == ""
        assert load_saliva_data.sample_times is None

    def test_upload_cortisol_plate(
        self, load_saliva_data, script_dir, saliva_plate_file_name
    ):
        load_saliva_data.format = "Plate Format"
        abs_file_path = os.path.join(script_dir, saliva_plate_file_name)
        with open(abs_file_path, "rb") as f:
            load_saliva_data.upload_btn.value = f.read()
            load_saliva_data.upload_btn.filename = saliva_plate_file_name
        assert load_saliva_data.temporary_dataframe is not None
        load_saliva_data.select_saliva.value = "Cortisol"
        load_saliva_data.select_sample_id_col.value = "sample ID"
        load_saliva_data.select_data_col.value = "cortisol (nmol/l)"
        load_saliva_data.process_plate_format()
        assert load_saliva_data.data is not None
        assert load_saliva_data.ready == True
