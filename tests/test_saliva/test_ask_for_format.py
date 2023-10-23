import pytest

from src.Saliva.ask_for_format import AskForFormat


class TestAskForFormat:
    @pytest.fixture
    def ask_for_format(self):
        return AskForFormat()

    def test_ask_for_format(self, ask_for_format):
        assert ask_for_format is not None
        assert ask_for_format.ready == False
        possible_formats = ask_for_format.format_selector.options
        assert possible_formats == ["", "Wide Format", "Plate Format"]

    def test_ask_for_format_plate(self, ask_for_format):
        ask_for_format.format_selector.value = "Plate Format"
        assert ask_for_format.ready == True
        assert ask_for_format.format == "Plate Format"
        ask_for_format.format_selector.value = ""
        assert ask_for_format.ready == False
        assert ask_for_format.format == ""
        ask_for_format.format_selector.value = "Wide Format"
        assert ask_for_format.ready == True
        assert ask_for_format.format == "Wide Format"
