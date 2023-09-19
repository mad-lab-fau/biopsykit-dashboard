import param
import panel as pn


class AskForFormat(param.Parameterized):
    condition_list = param.Dynamic(default=None)
    format_selector = pn.widgets.Select(
        options=["", "Wide Format", "Plate Format"],
        name="Format",
    )
    ready = param.Boolean(default=False)
    format = param.String(default=None)

    def format_changed(self, event):
        self.format = event.new
        self.ready = bool(event.new)

    @param.output(
        ("format", param.Dynamic),
    )
    def output(self):
        return (self.format,)

    def panel(self):
        self.format_selector.param.watch(self.format_changed, "value")
        return pn.Column(
            pn.pane.Markdown("# Choose the format your data is stored in"),
            self.format_selector,
        )
