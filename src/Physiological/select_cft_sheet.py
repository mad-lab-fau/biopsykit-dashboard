import panel as pn
import param

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import SELECT_CFT_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class SelectCFTSheet(PhysiologicalBase):
    select_cft_sheets = pn.widgets.CheckBoxGroup(
        sizing_mode="stretch_width",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = SELECT_CFT_TEXT
        super().__init__(**params)
        self.step = 6
        self.update_step(self.step)
        self.update_text(SELECT_CFT_TEXT)
        self.select_cft_sheets.link(self, callbacks={"value": self.sheet_checked})
        pane = pn.Column(self.header)
        pane.append(self.select_cft_sheets)
        self._view = pane

    def sheet_checked(self, _, event):
        if len(self.select_cft_sheets.value) == 0:
            self.ready = False
            self.cft_sheets = []
        else:
            self.ready = True
            self.cft_sheets = self.select_cft_sheets.value

    def panel(self):
        self.select_cft_sheets.options = list(self.data.keys())
        return self._view
