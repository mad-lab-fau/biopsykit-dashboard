import panel as pn
import param
import pytz


class SetSleepDataParameters(param.Parameterized):
    selected_device = param.String(default="")
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
    selected_parameters = param.Dict(default={})

    def show_parameters(self) -> pn.Column:
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

    @param.output("selected_device", param.String, "selected_parameters", param.Dict)
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
        )

    def panel(self):
        text = "# Set sleep data parameters \n Below you can set the parameters for the sleep data. If you are unsure, you can leave the default values."
        self.selected_parameters = self.parameters[self.selected_device]
        return pn.Column(pn.pane.Markdown(text), self.show_parameters())
