import param
import pytz

from src.Physiological.custom_components import PipelineHeader
from src.Sleep.SLEEP_CONSTANTS import SLEEP_MAX_STEPS


class SleepBase(param.Parameterized):
    selected_device = param.String(default="")
    step = param.Integer(default=1)
    parsing_parameters = {
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
            # "handle_counter_inconsistency": ["raise", "warn", "ignore"],
            "tz": [
                "None",
            ]
            + list(pytz.all_timezones),
        },
    }
    selected_parameters = param.Dynamic(
        default={
            "Withings": {
                "data_source": "heart_rate",
                "timezone": None,
                "split_into_nights": True,
            },
            "Polysomnography": {
                "datastreams": None,
                "tz": None,
            },
            "Other IMU Device": {
                # "handle_counter_inconsistency": ["raise", "warn", "ignore"],
                "tz": None,
            },
        }
    )
    data = param.Dynamic(default={})

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, SLEEP_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def add_data(self, parsed_file, filename: str):
        if filename in self.data.keys():
            self.data.remove(filename)
        self.data[filename] = parsed_file

    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
    )
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
        )
