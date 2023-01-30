import param
import panel as pn


class Session(param.Parameterized):
    step = 1
    max_steps = 20
    session = pn.widgets.Select(
        name="", value="Single Session", options=["Multiple Sessions", "Single Session"]
    )
    text = ""
    ready = param.Boolean(default=True)
    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )

    def get_step_static_text(self):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(self.step) + " of " + str(self.max_steps),
        )

    def set_progress_value(self):
        self.progress.value = int((self.step / self.max_steps) * 100)

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/number_of_sessions.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.set_progress_value()
        return pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            self.session,
        )

    @param.output(
        ("sess", param.Dynamic),
    )
    def output(self):
        return self.session
