import panel as pn

from src.Physiological.recordings import Recordings


class Compress(Recordings):
    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/Compress.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.step.value = "Step 4 of " + str(self.max_steps + 1)
        return pn.Column(
            pn.Row(self.step),
            pn.pane.Markdown(self.text),
        )
