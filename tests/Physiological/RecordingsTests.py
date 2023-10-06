import pytest
from src.Physiological.recordings import Recordings


@pytest.fixture
def recordings():
    return Recordings()


def test_constructor(recordings):
    """Tests default values of Recordings"""
    assert recordings.select_recording.options == [
        "Multiple Recording",
        "Single Recording",
    ]
    assert recordings.select_recording.value == "Single Recording"
    assert recordings.recording == "Single Recording"


def test_change_recordings(recordings):
    """Tests change of recordings"""
    recordings.select_recording.value = "Multiple Recording"
    assert recordings.next == "Multiple Files"
    recordings.select_recording.value = "Single Recording"
    assert recordings.next == "Upload Files"
