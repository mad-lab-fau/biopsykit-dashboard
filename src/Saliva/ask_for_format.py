import param
import panel as pn


class AskForFormat(param.Parameterized):
    condition_list = param.Dynamic(default=None)
    format_selector = pn.widgets.Select(
        options=["", "Wide Format", "Plate Format"],
        default="",
        name="Format",
    )
    ready = param.Boolean(default=False)
    format = param.String(default=None)

    def format_changed(self, event):
        self.ready = bool(event.new)
        self.format = event.new

    def panel(self):
        self.format_selector.param.watch(self.format_changed, "value")
        return pn.Column(
            pn.pane.Markdown("# Choose the format your data is stored in"),
            self.format_selector,
        )
