import panel as pn
import param

from src.Sleep.SLEEP_CONSTANTS import CHOOSE_DEVICE_TEXT, POSSIBLE_DEVICES
from src.Sleep.sleep_base import SleepBase


class ChooseRecordingDevice(SleepBase):
    ready = param.Boolean(default=False)
    device_selector = pn.widgets.Select(
        name="Device",
        sizing_mode="stretch_width",
        options=[""] + POSSIBLE_DEVICES,
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHOOSE_DEVICE_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(CHOOSE_DEVICE_TEXT)
        self.device_selector.link(self, callbacks={"value": self.device_changed})
        self._view = pn.Column(self.header, self.device_selector)

    def device_changed(self, _, event):
        self.selected_device = event.new
        self.ready = bool(event.new)

    def panel(self):
        self.device_selector.value = self.selected_device
        return self._view
