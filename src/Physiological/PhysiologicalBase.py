import param
import panel as pn


class PhysiologicalBase(param.Parameterized):
    selected_signal = param.String()
    selected_session = param.String()
    step = param.Integer(default=1)
    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )
    max_steps = param.Integer(default=12)

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)
