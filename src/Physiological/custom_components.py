from typing import Dict

import pandas as pd
import param
import panel as pn


class PipelineHeader(pn.viewable.Viewer):
    max_step = param.Integer(default=100)

    def __init__(
        self,
        step: int | param.Integer,
        max_step: int | param.Integer,
        text: str | param.String,
        **params
    ):
        self.max_step = max_step
        self._progress = pn.indicators.Progress(
            name="Progress",
            height=20,
            sizing_mode="stretch_width",
            max=max_step,
            value=step,
        )
        self._step_text = pn.widgets.StaticText(
            name="Progress", value="Step " + str(step) + " of " + str(max_step)
        )
        self.text = pn.pane.Markdown(text)
        super().__init__(**params)
        self._layout = pn.Column(
            pn.Row(self._step_text),
            pn.Row(self._progress),
            pn.Column(self.text),
        )

    def update_step(self, step: int):
        self._step_text.value = "Step " + str(step) + " of " + str(self.max_step)
        self._progress.value = step

    def update_text(self, text: str):
        self.text = pn.pane.Markdown(text)

    def __panel__(self):
        return self._layout


class Timestamp(pn.viewable.Viewer):

    value = param.Tuple(doc="First value is the name the second the timestamp")
    remove = False
    name = param.String()

    def __init__(self, **params):
        self._timestamp_name = pn.widgets.StaticText()
        self._timestamp_datetime = pn.widgets.DatetimePicker()
        self._timestamp_remove = pn.widgets.Button(name="Remove", button_type="primary")
        super().__init__(**params)
        self._layout = pn.Row(
            self._timestamp_name, self._timestamp_datetime, self._timestamp_remove
        )
        self._sync_widgets()
        # self._timestamp_remove.on_click(self.)

    def __panel__(self):
        return self._layout

    @param.depends("_timestamp_remove.value", watch=True)
    def remove_btn_click(self):
        self.remove = True

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        self._timestamp_name.value = self.value[0]
        self._timestamp_datetime.value = self.value[1]

    @param.depends("_timestamp_datetime.value", watch=True)
    def _sync_params(self):
        self.value = (self._timestamp_name.value, self._timestamp_datetime.value)


class TimestampList(pn.viewable.Viewer):

    value = param.List(doc="List of Tuples (str, DateTime)")
    col = pn.Column()
    timestamps = []
    name = param.String()

    def __init__(self, **params):
        super().__init__(**params)
        self._layout = self.col
        self._sync_widgets()

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        for nt in self.value:
            ts = Timestamp(name=nt[0], value=(nt[0], nt[1]))
            ts._timestamp_remove.on_click(self.remove_btn_click)
            self.col.append(ts)

    def __panel__(self):
        self._layout = self.col
        return self._layout

    def remove_btn_click(self, event):
        # Check all Items in
        print("In TimestampList")
        print(event)


class SubjectDataFrameView(pn.viewable.Viewer):
    def __init__(
        self, subjects: Dict[str, Dict[str, Dict[str, pd.DataFrame]]], **params
    ):
        self._subject_results_dict = subjects
        self.select_subject = pn.widgets.Select(name="Subject")
        if subjects is not None and len(subjects.keys()) > 0:
            self.select_subject.options = list(subjects.keys())
        self.select_subject.link(self, callbacks={"value": self.change_subject})
        self.select_result = pn.widgets.Select(name="Result", options=["init"])
        self.select_result.link(self, callbacks={"value": self.change_result})
        self.select_phase = pn.widgets.Select(name="Phase", options=[])
        self.select_phase.link(self, callbacks={"value": self.change_phase})
        self.tab = pn.widgets.Tabulator(
            name="Results",
            pagination="local",
            layout="fit_data_stretch",
            page_size=30,
            visible=False,
        )
        self._layout = pn.Column(
            pn.Row(self.select_subject, self.select_result, self.select_phase),
            self.tab,
        )
        super().__init__(**params)

    def set_subject_results(
        self, subjects: Dict[str, Dict[str, Dict[str, pd.DataFrame]]]
    ):
        self._subject_results_dict = subjects
        self.select_subject.options = list(subjects.keys())

    def change_subject(self, target, event):
        self.select_result.options = list(self._subject_results_dict[event.new].keys())
        subject = event.new
        result = self.select_result.value
        phase = self.select_phase.value
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def change_result(self, target, event):
        subject = self.select_subject.value
        result = event.new
        self.select_phase.options = list(
            self._subject_results_dict[subject][result].keys()
        )
        phase = self.select_phase.value
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def change_phase(self, target, event):
        subject = self.select_subject.value
        result = self.select_result.value
        phase = event.new
        if subject is None or result is None or phase is None:
            return
        df = self._subject_results_dict[subject][result][phase]
        self.tab.value = df
        self.tab.visible = True

    def __panel__(self):
        return self._layout
