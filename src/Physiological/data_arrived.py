import nilspodlib
import param
import panel as pn
import pandas as pd

from src.Physiological.CONSTANTS import DATA_ARRIVED_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class DataArrived(PhysiologicalBase):
    ready = param.Boolean(default=True)
    subject_selector = pn.widgets.Select()
    sampling_rate_input = pn.widgets.TextInput(
        name="Sampling rate Input", placeholder="Enter your sampling rate here..."
    )
    info_dict = None
    info_selection = pn.widgets.Select(
        name="Info header", options=[], visible=False, value=""
    )
    info_selected_value = pn.pane.Str("")
    next = param.Selector(
        objects=["Do you want to add time logs?", "Select CFT Sheet"],
        default="Do you want to add time logs?",
    )
    data_view = pn.widgets.Tabulator(
        pagination="local",
        layout="fit_data_stretch",
        page_size=20,
        header_align="right",
        visible=False,
    )
    session_start = pn.widgets.DatetimePicker(name="Session start:", disabled=True)
    session_end = pn.widgets.DatetimePicker(name="Session end:", disabled=True)

    def __init__(self, **params):
        params["HEADER_TEXT"] = DATA_ARRIVED_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.sampling_rate_input.link(
            self, callbacks={"value": self.set_sampling_rate_value}
        )
        self.info_selection.link(self, callbacks={"value": self.display_info_value})
        pane = pn.Column(self.header)
        pane.append(self.subject_selector)
        pane.append(self.sampling_rate_input)
        pane.append(self.session_start)
        pane.append(self.session_end)
        pane.append(self.data_view)
        self._view = pane

    def set_sampling_rate_value(self, target, event):
        self.ready = False
        if not self.sampling_rate_input.value:
            return
        try:
            self.sampling_rate = float(self.sampling_rate_input.value)
            self.ready = True
        except ValueError:
            pn.state.notifications.error(
                "Sampling rate must be a number (seperated by a .)"
            )

    def display_info_value(self, target, event):
        if (
            not self.info_selection.value
            or self.info_selection.value not in self.info_dict.keys()
        ):
            self.info_selected_value.object = ""
        else:
            self.info_selected_value.object = self.info_dict[self.info_selection.value]

    def subject_selected(self, event):
        if not event.new:
            return
        if self.data is None:
            return
        if isinstance(self.data[event.new], pd.DataFrame):
            self.data_view.value = self.data[event.new]
            self.data_view.visible = True

    def get_session_start_and_end(self, pane):
        start = pn.widgets.DatetimePicker(name="Session start:", disabled=True)
        end = pn.widgets.DatetimePicker(name="Session end:", disabled=True)
        accordion = pn.Accordion()
        if isinstance(self.data, dict) and all(
            isinstance(x, pd.DataFrame) for x in self.data.values()
        ):
            for key in self.data.keys():
                ds = self.data[key]
                accordion.append(pn.widgets.DataFrame(name=key, value=ds.head(20)))
            pane.append(accordion)
            return pane
        elif isinstance(self.data, dict) and all(
            isinstance(x, nilspodlib.Dataset) for x in self.data.values()
        ):
            for key in self.data.keys():
                ds = self.data[key]
                accordion.append(
                    pn.widgets.DataFrame(name=key, value=ds.data_as_df().head(20))
                )
            pane.append(accordion)
            return pane
        else:
            return pane

    def panel(self):
        if self.selected_signal == "CFT":
            self.next = "Select CFT Sheet"
        if self.sampling_rate == -1 and self.selected_signal != "CFT":
            if self.sampling_rate != -1:
                self.sampling_rate_input.value = str(self.sampling_rate)
            if self.sampling_rate_input.value == "":
                self.ready = False
            else:
                self.ready = True
        else:
            self.ready = True
        self.sampling_rate_input.value = str(self.sampling_rate)
        self.subject_selector.options = [""] + list(self.data.keys())
        self.subject_selector.value = ""
        self.subject_selector.visible = self.data is not None
        self.subject_selector.param.watch(self.subject_selected, "value")

        if type(self.data) == pd.DataFrame:
            self.data_view.value = self.data
            self.data_view.visible = True
        # elif type(self.data) == Session:
        #     self.data_view.value = self.data.data_as_df()[0]
        #     self.data_view.visible = True
        elif type(self.data) == dict:
            self.data_view.visible = False
        return self._view
