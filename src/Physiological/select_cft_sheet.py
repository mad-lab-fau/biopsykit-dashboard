import panel as pn
import param

from src.Physiological.data_arrived import DataArrived


class SelectCFTSheet(DataArrived):
    text = ""
    cft_sheet = pn.widgets.CheckBoxGroup()
    ready = param.Boolean(default=False)

    @pn.depends("cft_sheet.value", watch=True)
    def sheet_checked(self):
        if len(self.cft_sheet.value) == 0:
            self.ready = False
        else:
            self.ready = True

    @param.output(
        ("cft_sheets", param.Dynamic),
        ("data", param.Dynamic),
        ("selected_signal", param.Dynamic),
    )
    def output(self):
        return (self.cft_sheet.value, self.data, self.selected_signal)

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/SelectCFTSheet.md", "r")
            fileString = f.read()
            self.text = fileString
        self.cft_sheet.options = list(self.data.keys())
        return pn.Column(pn.pane.Markdown(self.text), self.cft_sheet)
