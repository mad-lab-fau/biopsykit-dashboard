import datetime as datetime
from typing import Dict, List

import pandas as pd
import param
import panel as pn
import biopsykit as bp
from biopsykit.signals._base import _BaseProcessor


class PipelineHeader(pn.viewable.Viewer):
    max_step = param.Integer(default=100)

    def __init__(
        self,
        step: int | param.Integer,
        max_step: int | param.Integer,
        text: str | param.String,
        **params,
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
            page_size=15,
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


class PlotViewer(pn.viewable.Viewer):
    def __init__(
        self,
        signal_type: str | None,
        signal: Dict[str, _BaseProcessor] | None,
        sampling_rate: float | None,
        **params,
    ):
        self._signal_type = signal_type
        self._signal = signal
        self._sampling_rate = sampling_rate
        self.select_result = pn.widgets.Select(name="Result")
        self.select_phase = pn.widgets.Select(name="Phase")
        if signal is not None:
            self.select_result.options = list(signal.keys())
        self.graph = pn.pane.Matplotlib()
        self.select_result.link(self.graph, callbacks={"value": self.change_result})
        self.select_phase.link(self.graph, callbacks={"value": self.change_phase})
        self._layout = pn.Column(
            pn.Row(self.select_result, self.select_phase), self.graph
        )
        super().__init__(**params)

    def set_signal_type(self, signal_type: str):
        self._signal_type = signal_type

    def set_sampling_rate(self, sampling_rate: float):
        self._sampling_rate = sampling_rate

    def set_values(
        self, signal_type: str, signal: Dict[str, _BaseProcessor], sampling_rate: float
    ):
        self._signal_type = signal_type
        self._signal = signal
        self._sampling_rate = sampling_rate
        self.select_result.options = list(signal.keys())

    def set_signal(self, signal: Dict[str, pd.DataFrame]):
        self._signal = signal
        self.select_result.options = list(signal.keys())

    def change_phase(self, target, event):
        phase = event.new
        subject = self.select_result.value
        if subject is None or phase is None:
            return
        if self._signal_type == "ECG" and self._signal is not None:
            self.select_phase.options = list()
            fig, _ = bp.signals.ecg.plotting.ecg_plot(
                ecg_processor=self._signal[subject],
                sampling_rate=self._sampling_rate,
                key=phase,
            )
            target.object = fig

    def change_result(self, target, event):
        if self._signal_type == "ECG" and self._signal is not None:
            self.select_phase.options = list()
            fig, _ = bp.signals.ecg.plotting.ecg_plot(
                ecg_processor=self._signal[event.new],
                sampling_rate=self._sampling_rate,
                key=self._signal[event.new].phases[0],
            )
            self.select_phase.options = self._signal[event.new].phases
            target.object = fig

    def __panel__(self):
        return self._layout


class TimesToSubject(pn.viewable.Viewer):

    accordion = pn.Accordion()
    subject_time_dict = param.Dict(default={})
    add_new_subject_selector = pn.widgets.Select(
        name="Add New Subject", align=("start", "end")
    )
    add_new_subject_btn = pn.widgets.Button(
        name="Add New Subject", button_type="primary", align=("start", "end")
    )
    files_to_subjects = {}
    ready = not any(files_to_subjects.values()) is None

    def __init__(self, subject_names: List[str], **params):
        super().__init__(**params)
        self.add_new_subject_selector.options = subject_names
        for subject in subject_names:
            self.files_to_subjects[subject] = None
        self.add_new_subject_btn.link(
            self.add_new_subject_selector, callbacks={"clicks": self.add_new_subject}
        )
        self._layout = pn.Column(
            self.accordion,
            pn.Row(self.add_new_subject_selector, self.add_new_subject_btn),
        )

    def initialize_filenames(self, filenames: List[str]):
        self.add_new_subject_selector.options = filenames
        for subject in filenames:
            self.files_to_subjects[subject] = None
        self.add_new_subject_btn.link(
            self.add_new_subject_selector, callbacks={"clicks": self.add_new_subject}
        )

    def assign_file_to_subject(self, target, _):
        new_subject = target[0]
        file_name = target[1].value
        self.files_to_subjects[file_name] = new_subject
        if file_name == "":
            pn.state.notifications.warning(
                f"Please assign a file to the subject {new_subject}"
            )
        else:
            pn.state.notifications.success(
                f"Successfully assigned file {file_name} to subject {new_subject}"
            )

    def add_new_subject_time_dict(
        self, new_subject_time_dict: Dict[str, Dict[str, pd.DataFrame]]
    ):
        for subject in new_subject_time_dict.keys():
            self.append_subject_to_accordion(subject, new_subject_time_dict[subject])

    def add_new_subject(self, target, _):
        if (
            target.value is None
            or target.value == ""
            or target.value in self.subject_time_dict.keys()
        ):
            pn.state.notifications.error("Subject already added")
            return
        self.files_to_subjects[target.value] = target.value
        self.append_subject_to_accordion(target.value)

    def append_subject_to_accordion(
        self, subject_name: str, time_dict: None | Dict[str, pd.DataFrame] = None
    ):
        if subject_name in self.subject_time_dict.keys():
            return
        self.subject_time_dict[subject_name] = time_dict
        self.accordion.append(self.get_subject_column(subject_name))

    def get_subject_column(self, subject_name: str) -> pn.Column:
        col = pn.Column(name=subject_name)
        rename_input = pn.widgets.TextInput(
            name=f"Rename Subject {subject_name}:", align=("start", "end")
        )
        new_phase_input = pn.widgets.TextInput(
            name="New Phase Name:", align=("start", "end")
        )
        add_phase_btn = pn.widgets.Button(
            name="Add Phase", button_type="primary", align=("start", "end")
        )
        add_phase_btn.link(
            (
                subject_name,
                new_phase_input,
                col,
            ),
            callbacks={"clicks": self.add_phase_to_subject},
        )
        remove_btn = pn.widgets.Button(
            name=f"Remove {subject_name}", button_type="danger", align=("start", "end")
        )
        if self.subject_time_dict[subject_name] is not None:
            associate_file_to_subject_selector = pn.widgets.Select(
                name="Subject",
                options=[""] + list(self.files_to_subjects.keys()),
                align=("start", "end"),
            )
            associate_file_to_subject_btn = pn.widgets.Button(
                name="Associate", button_type="primary", align=("start", "end")
            )
            associate_file_to_subject_btn.link(
                (
                    subject_name,
                    associate_file_to_subject_selector,
                ),
                callbacks={"clicks": self.assign_file_to_subject},
            )
            col.append(
                pn.Row(
                    associate_file_to_subject_selector,
                    associate_file_to_subject_btn,
                )
            )
            col.append(pn.layout.Divider())
            for phase in self.subject_time_dict[subject_name]:
                phase_name_input = pn.widgets.TextInput(
                    placeholder=phase, value=phase, align=("start", "end")
                )
                phase_name_input.link(
                    (
                        subject_name,
                        col,
                    ),
                    callbacks={"value": self.rename_phase},
                )
                remove_phase_btn = pn.widgets.Button(
                    name=f"Remove {phase}", button_type="danger", align=("start", "end")
                )
                remove_phase_btn.link(
                    (
                        subject_name,
                        phase,
                        col,
                    ),
                    callbacks={"clicks": self.remove_phase},
                )
                col.append(pn.Row(phase_name_input, remove_phase_btn))
                for subphase, time in (
                    self.subject_time_dict[subject_name][phase].items()
                    if self.subject_time_dict[subject_name][phase] is not None
                    else []
                ):
                    subphase_name_input = pn.widgets.TextInput(
                        value=subphase, align=("start", "end")
                    )
                    subphase_dt_picker = pn.widgets.DatetimePicker(
                        value=time, align=("start", "end")
                    )
                    subphase_remove_btn = pn.widgets.Button(
                        name="Remove", button_type="danger", align=("start", "end")
                    )
                    subphase_remove_btn.link(
                        (
                            subject_name,
                            phase,
                            subphase,
                            col,
                        ),
                        callbacks={"clicks": self.remove_subphase},
                    )
                    col.append(
                        pn.Row(
                            subphase_name_input,
                            subphase_dt_picker,
                            subphase_remove_btn,
                        )
                    )
                add_subphase_btn = pn.widgets.Button(
                    name="Add Subphase", button_type="primary"
                )
                add_subphase_btn.link(
                    (subject_name, phase, col),
                    callbacks={"clicks": self.add_subphase_btn_click},
                )
                col.append(pn.Row(pn.layout.HSpacer(), add_subphase_btn))
        col.append(pn.Row(new_phase_input, add_phase_btn))
        col.append(pn.layout.Divider())
        col.append(rename_input)
        col.append(remove_btn)
        rename_input.link(col, callbacks={"value": self.rename_subject})
        remove_btn.link(col, callbacks={"clicks": self.remove_subject})
        return col

    def add_subphase_btn_click(self, target, _):
        subject_name = target[0]
        phase = target[1]
        subject_col = target[2]
        new_phase_name = "New Subphase"
        if (
            self.subject_time_dict[subject_name][phase] is None
            or len(self.subject_time_dict[subject_name][phase]) == 0
        ):
            self.subject_time_dict[subject_name][phase] = pd.Series(
                {new_phase_name: datetime.datetime.now()}
            )
        elif new_phase_name not in list(
            self.subject_time_dict[subject_name][phase].index.values
        ):
            self.subject_time_dict[subject_name][phase] = pd.concat(
                [
                    self.subject_time_dict[subject_name][phase],
                    pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
                ]
            )
        elif new_phase_name in list(
            self.subject_time_dict[subject_name][phase].index.values
        ):
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in list(
                self.subject_time_dict[subject_name][phase].index.values
            ):
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
            self.subject_time_dict[subject_name][phase] = pd.concat(
                [
                    self.subject_time_dict[subject_name][phase],
                    pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
                ]
            )
        index = self.accordion.objects.index(subject_col)
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def add_phase_to_subject(self, target, _):
        subject_name = target[0]
        new_phase_name = target[1].value
        if new_phase_name is None or new_phase_name == "":
            pn.state.notifications.error("Phase name must be filled out")
            return
        if (
            self.subject_time_dict[subject_name] is not None
            and new_phase_name in self.subject_time_dict[subject_name].keys()
        ):
            pn.state.notifications.error("Phase already added")
            return
        if self.subject_time_dict[subject_name] is None:
            self.subject_time_dict[subject_name] = {new_phase_name: None}
        else:
            self.subject_time_dict[subject_name][new_phase_name] = None
        index = self.accordion.objects.index(target[2])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def rename_phase(self, target, event):
        subject_name = target[0]
        new_phase_name = event.new
        old_phase_name = event.old
        self.subject_time_dict[subject_name][new_phase_name] = self.subject_time_dict[
            subject_name
        ].pop(old_phase_name)
        index = self.accordion.objects.index(target[1])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def rename_subject(self, target, event):
        file_name = self.get_filename_of_subject(target.name)
        self.files_to_subjects[file_name] = event.new
        index = self.accordion.objects.index(target)
        self.subject_time_dict[event.new] = self.subject_time_dict.pop(target.name)
        col = self.get_subject_column(event.new)
        self.accordion.__setitem__(index, col)

    def get_filename_of_subject(self, subject_name: str) -> str:
        for file_name, subject in self.files_to_subjects.items():
            if subject == subject_name:
                return file_name
        return ""

    def remove_subphase(self, target, _):
        subject_name = target[0]
        phase = target[1]
        subphase = target[2]
        old_col = target[3]
        self.subject_time_dict[subject_name][phase].pop(subphase)
        index = self.accordion.objects.index(old_col)
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def remove_phase(self, target, _):
        subject_name = target[0]
        phase = target[1]
        self.subject_time_dict[subject_name].pop(phase)
        index = self.accordion.objects.index(target[2])
        col = self.get_subject_column(subject_name)
        self.accordion.__setitem__(index, col)

    def remove_subject(self, target, _):
        self.subject_time_dict.pop(target.name)
        self.accordion.remove(target)

    def get_subject_time_dict(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        return self.subject_time_dict

    def get_files_to_subjects(self) -> Dict[str, str]:
        return self.files_to_subjects

    def is_ready(self) -> bool:
        return not any(self.files_to_subjects.values()) is None

    def __panel__(self):
        return self._layout
