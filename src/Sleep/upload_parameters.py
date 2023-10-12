import panel as pn
import pytz

from src.Sleep.SLEEP_CONSTANTS import UPLOAD_PARAMETERS_TEXT
from src.Sleep.sleep_base import SleepBase


class SetSleepDataParameters(SleepBase):
    parameter_column = pn.Column()
    parameters = {
        "Withings": {
            "data_source": ["heart_rate", "respiration_rate", "sleep_state", "snoring"],
            "timezone": [
                "None",
            ]
            + list(pytz.all_timezones),
            "split_into_nights": True,
        },
        "Polysomnography": {
            "datastreams": None,
            "tz": [
                "None",
            ]
            + list(pytz.all_timezones),
        },
        "Other IMU Device": {
            "handle_counter_inconsistency": ["raise", "warn", "ignore"],
            "timezone": [
                "None",
            ]
            + list(pytz.all_timezones),
        },
    }

    def show_parameters(self) -> pn.Column:
        if self.selected_device == "":
            return pn.Column()
        possible_parameters = self.parameters[self.selected_device]
        col = pn.Column()
        for parameter, options in possible_parameters.items():
            if options is None:
                continue
            if isinstance(options, list):
                widget = pn.widgets.Select(
                    name=parameter,
                    options=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
            elif isinstance(options, bool):
                widget = pn.widgets.Checkbox(
                    name=parameter,
                    value=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
        return col

    def parameter_changed(self, event):
        self.selected_parameters[event.obj.name] = event.new

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(UPLOAD_PARAMETERS_TEXT)
        self._view = pn.Column(self.header, self.parameter_column)

    def panel(self):
        if self.selected_device != "":
            self.selected_parameters = self.parameters[self.selected_device]
        self.parameter_column.__setitem__(0, self.show_parameters())
        return self._view
