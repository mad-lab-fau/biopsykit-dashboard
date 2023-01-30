import panel as pn

from src.Physiological.recordings import Recordings


class Compress(Recordings):
    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/Compress.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.step = 2
        self.set_progress_value()
        return pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
        )
