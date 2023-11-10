import param
import pytz
import panel as pn
from src.Physiological.custom_components import PipelineHeader
from src.Sleep.SLEEP_CONSTANTS import SLEEP_MAX_STEPS


class SleepBase(param.Parameterized):
    data = param.Dynamic(default={})
    selected_device = param.String(default="")
    step = param.Integer(default=1)
    sampling_rate = param.Dynamic(default=256.0)
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
    processed_data = param.Dynamic(default={})
    selected_parameters = param.Dynamic(
        default={
            "Withings": {
                "data_source": "heart_rate",
                "timezone": "Europe/Berlin",
                "split_into_nights": True,
            },
            "Polysomnography": {
                "datastreams": None,
                "tz": "Europe/Berlin",
            },
            "Other IMU Device": {
                # "handle_counter_inconsistency": ["raise", "warn", "ignore"],
                "tz": "Europe/Berlin",
            },
        }
    )
    possible_processing_parameters = {
        "acceleration": {
            "convert_to_g": True,
            # "sampling_rate": 256.0,
            "algorithm_type": [
                "cole_kripke",
                "sadeh",
                "sazonov",
                "webster",
                "scripps_clinic",
                "cole_kripke_old",
            ],
            "epoch_length": 60,
        },
        "actigraph": {
            "algorithm_type": [
                "cole_kripke",
                "sadeh",
                "sazonov",
                "webster",
                "scripps_clinic",
                "cole_kripke_old",
            ],
            "bed_interval": [],
        },
    }
    processing_parameters = {
        "acceleration": {
            "convert_to_g": True,
            # "sampling_rate": 256.0,
            "algorithm_type": None,
            "epoch_length": 60,
        },
        "actigraph": {
            "algorithm_type": None,
            "bed_interval": [],
        },
    }

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
            self.data.pop(filename)
        self.data[filename] = parsed_file
        pn.state.notifications.success(f"Added {filename} to data")
        print(len(self.data[filename]))

    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
        ("processing_parameters", param.Dict),
        ("processed_data", param.Dynamic),
        ("possible_processing_parameters", param.Dict),
    )
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
            self.processing_parameters,
            self.processed_data,
            self.possible_processing_parameters,
        )
