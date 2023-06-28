import pytest

from src.Physiological.sessions import Session


@pytest.fixture
def session():
    return Session()


def test_constructor(session):
    """Tests default values of Session"""
    assert session.ready == True
    assert session.step == 1
    assert session.max_steps == 10
    assert session.session.value == "Single Session"
    assert session.selected_signal == ""


def test_output(session):
    """Tests output of Session"""
    session.selected_signal = "ECG"
    session.session = "Single Session"
    assert session.output() == ("Single Session", "ECG")
    with pytest.raises(Exception):
        session.session = "False Sessions"
    assert session.output() == ("Single Session", "ECG")
    session.session = "Multiple Sessions"
    assert session.output() == ("Multiple Sessions", "ECG")
