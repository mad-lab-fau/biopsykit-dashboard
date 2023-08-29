import pytest
from src.Physiological.recordings import Recordings


@pytest.fixture
def recordings():
    return Recordings()


def test_constructor(recordings):
    """Tests default values of Recordings"""
    assert recordings.ready == True
    assert recordings.recording == "Single Recording"
    assert recordings.selected_signal == ""


def test_change_recordings(recordings):
    """Tests change of recordings"""
    recordings.recording = "Multiple Recording"
    assert recordings.next == "Multiple Files"
    recordings.recording = "Single Recording"
    assert recordings.next == "Upload Files"
    with pytest.raises(Exception):
        recordings.recording = "False Recording"
    assert recordings.next == "Upload Files"
