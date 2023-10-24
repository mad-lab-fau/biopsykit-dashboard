import math

import nilspodlib
import param
import panel as pn
import pandas as pd

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import DATA_ARRIVED_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class DataArrived(PhysiologicalBase):
    ready = param.Boolean(default=False)
    subject_selector = pn.widgets.Select(
        sizing_mode="stretch_width",
    )
    sampling_rate_input = pn.widgets.TextInput(
        name="Sampling rate Input",
        placeholder="Enter your sampling rate here...",
        sizing_mode="stretch_width",
    )
    info_selected_value = pn.pane.Str("")
    next = param.Selector(
        objects=["Do you want to add time logs?", "Select CFT Sheet", "Data arrived"],
        default="Do you want to add time logs?",
    )
    data_view = pn.widgets.Tabulator(
        pagination="local",
        layout="fit_data_stretch",
        page_size=20,
        header_align="right",
        visible=False,
        disabled=True,
        sizing_mode="stretch_width",
    )
    session_start = pn.widgets.DatetimePicker(
        name="Session start:", disabled=True, sizing_mode="stretch_width", visible=False
    )
    session_end = pn.widgets.DatetimePicker(
        name="Session end:",
        disabled=True,
        sizing_mode="stretch_width",
        visible=False,
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = DATA_ARRIVED_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.sampling_rate_input.link(
            self, callbacks={"value": self.set_sampling_rate_value}
        )
        self.subject_selector.link(self, callbacks={"value": self.subject_selected})
        self._view = pn.Column(
            self.header,
            self.subject_selector,
            self.sampling_rate_input,
            self.session_start,
            self.session_end,
            self.data_view,
        )

    def set_sampling_rate_value(self, _, event):
        self.sampling_rate = self.convert_str_to_float(event.new)
        if self.sampling_rate > 0:
            self.ready = True
        else:
            pn.state.notifications.error(
                "Sampling rate must be a number (seperated by a .)"
            )
            self.ready = False

    @staticmethod
    def convert_str_to_float(str_value: str) -> float:
        try:
            float_value = float(str_value)
            if math.isnan(float_value):
                return -1.0
            return float_value
        except ValueError:
            return -1.0

    def subject_selected(self, _, event):
        if not event.new:
            self.session_end.visible = False
            self.session_start.visible = False
            self.data_view.visible = False
            return
        if self.data is None:
            self.session_end.visible = False
            self.session_start.visible = False
            self.data_view.visible = False
            return
        if isinstance(self.data[event.new], pd.DataFrame):
            self.data_view.value = self.data[event.new]
            self.data_view.visible = True
        self.set_session_start_and_end()

    def set_session_start_and_end(self):
        if (
            self.subject_selector.value is None
            or self.subject_selector.value == ""
            or self.data is None
            or self.subject_selector.value not in list(self.data.keys())
        ):
            return
        if isinstance(self.data[self.subject_selector.value], pd.DataFrame):
            ds = self.data[self.subject_selector.value]
            self.session_start.value = ds.index[0]
            self.session_end.value = ds.index[-1]
        elif isinstance(self.data[self.subject_selector.value], nilspodlib.Dataset):
            ds = self.data[self.subject_selector.value]
            self.session_start.value = ds.start_time
            self.session_end.value = ds.end_time
        self.session_start.visible = True
        self.session_end.visible = True

    def panel(self):
        if self.signal == "CFT":
            self.next = "Select CFT Sheet"
        elif self.signal == "RSP":
            self.next = "Set RSP Parameters"
        else:
            self.next = "Do you want to add time logs?"
        if self.sampling_rate > 0:
            self.sampling_rate_input.value = str(self.sampling_rate)
            self.ready = True
        else:
            self.sampling_rate_input.value = ""
            self.ready = False
            pn.state.notifications.warning("Please provide a sampling rate")
        self.subject_selector.options = [""] + list(self.data.keys())
        self.subject_selector.value = ""
        self.subject_selector.visible = self.data is not None
        self.data_view.visible = self.data is not None
        return self._view
