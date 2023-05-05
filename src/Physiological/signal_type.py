import panel as pn
import param


class PhysSignalType(param.Parameterized):
    text = ""
    ready = param.Boolean(default=False)
    pane = pn.Column()
    selected_signal = param.String(default="ECG")
    options = ["ECG", "CFT", "RSP", "EEG"]

    def signal_selected(self, event):
        self.selected_signal = event.obj.name
        self.ready = True

    @param.output(
        ("selected_signal", param.String()),
    )
    def output(self):
        return (self.selected_signal,)

    def panel(self):
        self.step = 5
        if self.text == "":
            f = open("../assets/Markdown/PhysSignalType.md", "r")
            fileString = f.read()
            self.text = fileString
        self.pane = pn.Column(pn.pane.Markdown(self.text))
        row = pn.Row()
        for option in self.options:
            btn = pn.widgets.Button(name=option, button_type="primary")
            btn.on_click(self.signal_selected)
            row.append(btn)
        self.pane.append(row)
        return self.pane
