import pytest
import panel as pn

from src.Sleep.SLEEP_CONSTANTS import POSSIBLE_DEVICES
from src.Sleep.set_sleep_data_parameters import SetSleepDataParameters


class TestSetSleepDataParameters:
    @pytest.fixture
    def set_sleep_data_parameters(self):
        return SetSleepDataParameters()

    @staticmethod
    def valid_parameters_are_shown(
        parameter_column: pn.Column,
        selected_device: str,
        set_sleep_data_parameters: SetSleepDataParameters,
    ) -> bool:
        for input_widget in parameter_column.objects:
            if (
                input_widget.name
                not in set_sleep_data_parameters.parsing_parameters[selected_device]
            ):
                return False
        return True

    def test_set_sleep_data_parameters_constructor(self, set_sleep_data_parameters):
        assert set_sleep_data_parameters is not None

    def test_set_sleep_data_parameters_show_parameters(self, set_sleep_data_parameters):
        col = set_sleep_data_parameters.get_parameter_column_for_selected_device()
        assert len(col.objects) == 0
        set_sleep_data_parameters.selected_device = "Polysomnography"
        col = set_sleep_data_parameters.get_parameter_column_for_selected_device()
        assert len(col.objects) > 0
        assert self.valid_parameters_are_shown(
            col, "Polysomnography", set_sleep_data_parameters
        )
        set_sleep_data_parameters.selected_device = "Withings"
        col = set_sleep_data_parameters.get_parameter_column_for_selected_device()
        assert len(col.objects) > 0
        assert self.valid_parameters_are_shown(
            col, "Withings", set_sleep_data_parameters
        )

    def test_set_sleep_parameters_select_all_parameters(
        self, set_sleep_data_parameters
    ):
        possible_devices = POSSIBLE_DEVICES
        for device in possible_devices:
            set_sleep_data_parameters.selected_device = device
            set_sleep_data_parameters.panel()
            for input_widget in set_sleep_data_parameters.parameter_column.objects:
                if isinstance(input_widget, pn.widgets.Select):
                    input_widget.value = input_widget.options[0]
                    assert (
                        set_sleep_data_parameters.selected_parameters[
                            "Polysomnography"
                        ][input_widget.name]
                        == input_widget.options[0]
                    )
                elif isinstance(input_widget, pn.widgets.Checkbox):
                    input_widget.value = True
                    assert (
                        set_sleep_data_parameters.selected_parameters[
                            "Polysomnography"
                        ][input_widget.name]
                        == input_widget.value
                    )
                    input_widget.value = False
                    assert (
                        set_sleep_data_parameters.selected_parameters[
                            "Polysomnography"
                        ][input_widget.name]
                        == input_widget.value
                    )
