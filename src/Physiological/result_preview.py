import panel as pn

from src.Physiological.process_hrv import AskToProcessHRV


class ResultsPreview(AskToProcessHRV):
    textHeader = ""

    def panel(self):
        if self.textHeader == "":
            f = open("../assets/Markdown/ProcessingAndPreview.md", "r")
            fileString = f.read()
            self.textHeader = fileString
        column = pn.Column(self.textHeader)
        return column
