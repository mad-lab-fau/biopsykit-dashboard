import pytest

from src.Physiological.sessions import Session


class TestSession:
    @pytest.fixture
    def session(self):
        return Session()

    def test_constructor(self, session):
        """Tests default values of Session"""
        assert session.ready == False
        assert session.session == "Single Session"
        assert session.signal == ""
        assert session.select_session.value == "Single Session"
        assert session.select_session.options == ["Multiple Sessions", "Single Session"]

    def test_output(self, session):
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
