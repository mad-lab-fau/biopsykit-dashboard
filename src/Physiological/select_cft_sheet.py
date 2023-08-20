import panel as pn
import param

from src.Physiological.data_arrived import DataArrived


class SelectCFTSheet(DataArrived):
    text = ""
    cft_sheet = pn.widgets.CheckBoxGroup()
    ready = param.Boolean(default=False)

    def __init__(self):
        super().__init__()
        self.step = 6
        text = (
            "# Select CFT Sheet \n\n"
            "This step allows you to select a CFT sheet from a list "
            "of available sheets."
        )
        self.cft_sheet.link(self, callbacks={"value": self.sheet_checked})
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(pn.Row(self.get_progress(self.step))))
        pane.append(pn.pane.Markdown(text))
        pane.append(self.cft_sheet)
        self._view = pane

    def sheet_checked(self, target, event):
        if len(self.cft_sheet.value) == 0:
            self.ready = False
        else:
            self.ready = True

    def panel(self):
        self.cft_sheet.options = list(self.data.keys())
        return self._view
