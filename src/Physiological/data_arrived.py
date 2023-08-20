import nilspodlib
import param
import panel as pn
import pandas as pd
from nilspodlib import Session

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class DataArrived(PhysiologicalBase):
    data = param.Dynamic()
    sampling_rate = param.Number()
    time_log_present = param.Boolean(default=False)
    time_log = param.Dynamic()
    synced = param.Boolean(default=False)
    session = param.String()
    sensors = param.Dynamic()
    timezone = param.String()
    selected_signal = param.String()
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

    def __init__(self):
        super().__init__()
        self.step = 5
        text = (
            "# Files uploaded successfully \n"
            "Below is a short summary of the files which you uploaded."
            "These files can be further analysed in the following steps."
        )
        pane = pn.Column(pn.Row(self.get_step_static_text(self.step)))
        pane.append(pn.Row(self.get_progress(self.step)))
        pane.append(pn.pane.Markdown(text))
        pane.append(self.subject_selector)
        pane.append(self.sampling_rate_input)
        pane.append(self.session_start)
        pane.append(self.session_end)
        pane.append(self.data_view)
        self._view = pane

    @pn.depends("sampling_rate_input.value", watch=True)
    def set_sampling_rate_value(self):
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

    @pn.depends("info_selection.value", watch=True)
    def display_info_value(self):
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

    @param.output(
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("sensors", param.Dynamic),
        ("time_log_present", param.Dynamic),
        ("time_log", param.Dynamic),
        ("timezone", param.String()),
    )
    def output(self):
        return (
            self.data,
            self.sampling_rate,
            self.sensors,
            self.time_log_present,
            self.time_log,
            self.timezone,
        )

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
