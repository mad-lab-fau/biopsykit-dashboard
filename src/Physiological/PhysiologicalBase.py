import pandas as pd
import param
import panel as pn
import datetime as datetime


class PhysiologicalBase(param.Parameterized):
    step = param.Integer(default=1)
    max_steps = param.Integer(default=12)
    progress = pn.indicators.Progress(
        name="Progress", height=20, sizing_mode="stretch_width"
    )
    times = None
    select_vp = pn.widgets.Select(
        name="Select Subject",
        visible=False,
    )

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    @staticmethod
    def get_progress(step) -> pn.indicators.Progress:
        return pn.indicators.Progress(
            name="Progress", height=20, sizing_mode="stretch_width", max=12, value=step
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)

    def select_vp_changed(self, _, event):
        self.subject = event.new

    def dict_to_column(self):
        if self.session == "Single Session" and len(self.subject_time_dict.keys()) > 1:
            self.select_vp.options = list(self.subject_time_dict.keys())
            self.select_vp.visible = True
            self.select_vp.link(
                "subject",
                callbacks={"value": self.select_vp_changed},
            )
            self.subject = list(self.subject_time_dict.keys())[0]
            self.ready = True
        timestamps = []
        for subject in self.subject_time_dict.keys():
            col = pn.Column()
            for condition in self.subject_time_dict[subject].keys():
                cond = pn.widgets.TextInput(value=condition)
                cond.link(
                    (subject, condition),
                    callbacks={"value": self.change_condition_name},
                )
                btn_remove_phase = pn.widgets.Button(
                    name="Remove Phase", button_type="danger"
                )
                btn_remove_phase.link(
                    (subject, condition),
                    callbacks={"value": self.remove_btn_click},
                )
                col.append(pn.Row(cond, btn_remove_phase))
                for phase, time in self.subject_time_dict[subject][condition].items():
                    row = pn.Row()
                    phase_name_input = pn.widgets.TextInput(value=phase)
                    phase_name_input.link(
                        (subject, condition, phase),
                        callbacks={"value": self.change_phase_name},
                    )
                    row.append(phase_name_input)
                    dt_picker = pn.widgets.DatetimePicker(value=time)
                    dt_picker.link(
                        (subject, condition, phase),
                        callbacks={"value": self.timestamp_changed},
                    )
                    row.append(dt_picker)
                    remove_btn = pn.widgets.Button(name="Remove", button_type="danger")
                    remove_btn.link(
                        (subject, condition, phase),
                        callbacks={"value": self.remove_btn_click},
                    )
                    row.append(remove_btn)
                    col.append(row)
                btn_subphase = pn.widgets.Button(
                    name="Add Subphase", button_type="primary"
                )
                btn_subphase.link(
                    (subject, condition),
                    callbacks={"value": self.add_subphase_btn_click},
                )
                row = pn.Row(pn.layout.HSpacer(), pn.layout.HSpacer(), btn_subphase)
                col.append(row)
            btn = pn.widgets.Button(name="Add Phase", button_type="primary")
            btn.link(
                (subject,),
                callbacks={"value": self.add_phase_btn_click},
            )
            col.append(btn)
            timestamps.append((subject, col))
        self.times.objects = [pn.Accordion(objects=timestamps)]

    def add_phase_btn_click(self, target, _):
        new_phase_name = "New Phase"
        self.subject_time_dict[target[0]][new_phase_name] = pd.Series(
            {"New Subphase": datetime.datetime.now()}
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active

    def add_subphase_btn_click(self, target, event):
        new_phase_name = "New Subphase"
        if new_phase_name in list(
            self.subject_time_dict[target[0]][target[1]].index.values
        ):
            i = 1
            new_phase_name = new_phase_name + " " + str(i)
            while new_phase_name in list(
                self.subject_time_dict[target[0]][target[1]].index.values
            ):
                i += 1
                new_phase_name = new_phase_name + " " + str(i)
        self.subject_time_dict[target[0]][target[1]] = pd.concat(
            [
                self.subject_time_dict[target[0]][target[1]],
                pd.Series(data=[datetime.datetime.now()], index=[new_phase_name]),
            ]
        )
        active = self.times.objects[0].active
        self.dict_to_column()
        self.times.objects[0].active = active
