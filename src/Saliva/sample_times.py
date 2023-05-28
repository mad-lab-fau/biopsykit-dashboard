import param
import panel as pn


class SetSampleTimes(param.Parameterized):
    data = param.Dynamic(default=None)
    saliva_type = param.String(default=None)
    sample_times = param.Dynamic(default=None)
    sample_times_input = pn.widgets.ArrayInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
    )
    ready = param.Boolean(default=False)

    def sample_times_changed(self, event):
        self.sample_times = event.new
        if self.sample_times is None or len(self.sample_times) == 0:
            self.ready = False
        else:
            self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.saliva_type,
            self.sample_times,
        )

    def panel(self):
        self.sample_times_input.param.watch(self.sample_times_changed, "value")
        return pn.Column(
            pn.pane.Markdown("# Enter the sample times"),
            self.sample_times_input,
        )
