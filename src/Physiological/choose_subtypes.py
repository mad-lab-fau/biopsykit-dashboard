import param
import panel as pn

from src.Physiological.process_hrv import ProcessHRV


class ChooseSubtypes(ProcessHRV):
    sampling_rate = param.Dynamic()
    text = ""
    sensors = param.Dynamic()

    def panel(self, f=None):
        if self.text == "":
            f = open("../assets/Markdown/ChooseSubtypes.md", "r")
            fileString = f.read()
            self.text = fileString
        pane = pn.Column(pn.pane.Markdown(self.text))
        return pane
