import pytest

from src.Physiological.sessions import Session


@pytest.fixture
def session():
    return Session()


def test_constructor(session):
    """Tests default values of Session"""
    assert session.ready == False
    assert session.session == "Single Session"
    assert session.signal == ""
    assert session.select_session.value == "Single Session"
    assert session.select_session.options == ["Multiple Sessions", "Single Session"]


def test_output(session):
    """Tests output of Session"""
    session.signal = "ECG"
    assert session.session == "Single Session"
    session.select_session.value = ""
    assert session.ready == False
    session.select_session.value = "Single Session"
    assert session.ready == True
    session.select_session.value = "Multiple Sessions"
    assert session.ready == True
    assert session.session == "Multiple Sessions"
