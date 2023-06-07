import panel as pn
import param


class ChooseRecordingDevice(param.Parameterized):
    possible_devices = [
        "",
        "Polysomnography",
        "Other IMU Device",
        "Withings",
    ]
    selected_device = param.String(default="")
    ready = param.Boolean(default=False)

    def device_changed(self, event):
        self.selected_device = event.new
        self.ready = bool(event.new)

    @param.output("selected_device", param.String)
    def output(self):
        return (self.selected_device,)

    def panel(self):
        text = "# Choose the recording device \n Below you can choose the device you used to record your sleep data. If you used a different device, please choose 'Other IMU Device'."
        select_device_widget = pn.widgets.Select(
            name="Device",
            options=self.possible_devices,
            value=self.selected_device,
        )
        select_device_widget.param.watch(self.device_changed, "value")
        return pn.Column(pn.pane.Markdown(text), select_device_widget)
