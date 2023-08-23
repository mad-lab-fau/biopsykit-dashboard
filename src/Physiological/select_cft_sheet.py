import panel as pn
import param

from src.Physiological.CONSTANTS import SELECT_CFT_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.data_arrived import DataArrived


class SelectCFTSheet(PhysiologicalBase):
    text = ""
    cft_sheet = pn.widgets.CheckBoxGroup()
    ready = param.Boolean(default=False)

    def __init__(self):
        super().__init__()
        self.step = 6
        self.update_step(self.step)
        self.update_text(SELECT_CFT_TEXT)
        self.cft_sheet.link(self, callbacks={"value": self.sheet_checked})
        pane = pn.Column(self.header)
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
