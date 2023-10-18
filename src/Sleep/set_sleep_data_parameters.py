import panel as pn

from src.Sleep.SLEEP_CONSTANTS import UPLOAD_PARAMETERS_TEXT
from src.Sleep.sleep_base import SleepBase


class SetSleepDataParameters(SleepBase):
    parameter_column = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = UPLOAD_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(UPLOAD_PARAMETERS_TEXT)
        self._view = pn.Column(self.header, self.parameter_column)

    def get_parameter_column_for_selected_device(self) -> pn.Column:
        col = pn.Column()
        if self.selected_device == "":
            return col
        possible_parameters = self.parsing_parameters[self.selected_device]
        for parameter, options in possible_parameters.items():
            set_value = self.selected_parameters[self.selected_device][parameter]
            if options is None:
                continue
            if isinstance(options, list):
                widget = pn.widgets.Select(
                    name=parameter,
                    options=options,
                    value=set_value if set_value is not None else options[0],
                )
            elif isinstance(options, bool):
                widget = pn.widgets.Checkbox(
                    name=parameter,
                    value=set_value,
                )
            else:
                continue
            widget.link(widget.name, callbacks={"value": self.parameter_changed})
            col.append(widget)
        return col

    def parameter_changed(self, target, event):
        if self.selected_device == "":
            pn.state.notifications.error("No device selected")
            return
        if target not in self.parsing_parameters[self.selected_device].keys():
            pn.state.notifications.error(
                f"{target} not found in parameters for {self.selected_device}"
            )
            return
        if event.new == "None":
            self.selected_parameters[self.selected_device][target] = None
        else:
            self.selected_parameters[self.selected_device][target] = event.new
        pn.state.notifications.success(f"{target} changed to {event.new}")

    def panel(self):
        if len(self.parameter_column.objects) == 0:
            self.parameter_column.append(
                self.get_parameter_column_for_selected_device()
            )
        else:
            self.parameter_column.__setitem__(
                0, self.get_parameter_column_for_selected_device()
            )
        return self._view
