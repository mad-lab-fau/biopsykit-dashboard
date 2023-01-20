import param
import panel as pn


class Session(param.Parameterized):
    max_steps = 20
    session = pn.widgets.Select(
        name="", value="Single Session", options=["Multiple Sessions", "Single Session"]
    )
    text = ""
    ready = param.Boolean(default=True)
    progress = pn.indicators.Progress(
        name="Progress", value=0, bar_color="primary", width=300
    )
    step = pn.widgets.StaticText(name="Progress", value="Step 1 of " + str(max_steps))

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/number_of_sessions.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        return pn.Column(
            pn.Row(self.step, self.progress),
            pn.pane.Markdown(self.text),
            self.session,
        )

    @param.output(
        ("sess", param.Dynamic),
    )
    def output(self):
        return self.session
