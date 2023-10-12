import panel as pn
import param

from src.Sleep.SLEEP_CONSTANTS import CHOOSE_DEVICE_TEXT
from src.Sleep.sleep_base import SleepBase


class ChooseRecordingDevice(SleepBase):
    possible_devices = [
        "",
        "Polysomnography",
        "Other IMU Device",
        "Withings",
    ]
    ready = param.Boolean(default=False)
    select_device_widget = pn.widgets.Select(
        name="Device",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHOOSE_DEVICE_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(CHOOSE_DEVICE_TEXT)
        self.select_device_widget.link(self, callbacks={"value": self.device_changed})
        self._view = pn.Column(self.header, self.select_device_widget)

    def device_changed(self, _, event):
        self.selected_device = event.new
        self.ready = bool(event.new)

    def panel(self):
        self.select_device_widget.options = self.possible_devices
        self.select_device_widget.value = self.selected_device
        return self._view
