import pytest

from src.Saliva.condition_list import AskToLoadConditionList, AddConditionList


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
