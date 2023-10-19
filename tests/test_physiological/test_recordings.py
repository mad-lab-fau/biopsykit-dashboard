import pytest
from src.Physiological.recordings import Recordings


class TestRecordings:
    @pytest.fixture
    def recordings(self):
        return Recordings()

    def test_constructor(self, recordings):
        """Tests default values of Recordings"""
        assert recordings.select_recording.options == [
            "Multiple Recording",
            "Single Recording",
        ]
        assert recordings.select_recording.value == "Single Recording"
        assert recordings.recording == "Single Recording"

    def test_change_recordings(self, recordings):
        """Tests change of recordings"""
        recordings.select_recording.value = "Multiple Recording"
        assert recordings.next == "Multiple Files"
        recordings.select_recording.value = "Single Recording"
        assert recordings.next == "Upload Files"
