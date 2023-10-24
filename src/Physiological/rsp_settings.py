import panel as pn

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import SET_RSP_PARAMETERS_TEXT, EDR_TYPES
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class SetRspParameters(PhysiologicalBase):
    checkbox_estimate_rsp = pn.widgets.Checkbox(name="Estimate RSP", value=False)
    select_estimation_method = pn.widgets.Select(
        name="Estimation Method",
        options=EDR_TYPES,
        visible=False,
        sizing_mode="stretch_width",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SET_RSP_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.checkbox_estimate_rsp.link(
            self.select_estimation_method,
            callbacks={"value": self.checkbox_estimate_changed},
        )
        self.select_estimation_method.link(
            self, callbacks={"value": self.change_estimation_method}
        )
        self._view = pn.Column(
            self.header, self.checkbox_estimate_rsp, self.select_estimation_method
        )

    def change_estimation_method(self, _, event):
        self.estimate_rsp_method = event.new

    def checkbox_estimate_changed(self, _, event):
        self.select_estimation_method.visible = event.new
        self.estimate_rsp = event.new

    def panel(self):
        return self._view
