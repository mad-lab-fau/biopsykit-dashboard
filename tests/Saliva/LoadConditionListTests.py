import os

import pandas as pd
import pytest
import os
from src.Saliva.condition_list import AskToLoadConditionList, AddConditionList


@pytest.fixture
def script_dir():
    return os.path.join(os.path.dirname(__file__), "example_data")


@pytest.fixture
def condition_list_filename():
    return "cond_list.csv"


@pytest.fixture
def ask_to_load_condition_list():
    return AskToLoadConditionList()


@pytest.fixture
def add_condition_list():
    return AddConditionList()


def test_constructor_ask_to_load_condition_list_(ask_to_load_condition_list):
    assert ask_to_load_condition_list is not None
    assert ask_to_load_condition_list.ready == False
    assert ask_to_load_condition_list.next_page == "Add Condition List"
    ask_to_load_condition_list.no_condition_list_btn.clicks += 1
    assert ask_to_load_condition_list.ready == True
    assert ask_to_load_condition_list.next_page == "Load Saliva Data"
    ask_to_load_condition_list.add_condition_list_btn.clicks += 1
    assert ask_to_load_condition_list.ready == True
    assert ask_to_load_condition_list.next_page == "Add Condition List"


def test_constructor_load_condition_list(add_condition_list):
    assert add_condition_list is not None
    assert add_condition_list.ready == False
    assert add_condition_list.upload_condition_list_btn.accept == ".csv,.xls,.xlsx"
    assert add_condition_list.upload_condition_list_btn.multiple == False


def test_upload_condition_list(add_condition_list, condition_list_filename, script_dir):
    abs_file_path = os.path.join(script_dir, condition_list_filename)
    with open(abs_file_path, "rb") as f:
        add_condition_list.upload_condition_list_btn.filename = condition_list_filename
        add_condition_list.upload_condition_list_btn.value = f.read()
    assert add_condition_list.condition_list is not None
    assert add_condition_list.ready == True
    assert add_condition_list.condition_list.shape == (28, 1)
