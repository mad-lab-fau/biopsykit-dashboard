import numpy as np
import panel as pn
import param

from src.Physiological.add_times import AskToAddTimes


class FrequencyBands(AskToAddTimes):
    text = ""
    band_panel = pn.Column()

    freq_bands = {
        "theta": [4, 8],
        "alpha": [8, 13],
        "beta": [13, 30],
        "gamma": [30, 44],
    }

    def show_freq_bands(self):
        pane = pn.Column()
        for key, value in self.freq_bands.items():
            remove_btn = pn.widgets.Button(name="Remove")
            remove_btn.link(
                (key),
                callbacks={"value": self.remove_band},
            )
            band_name_input = pn.widgets.TextInput(value=key)
            band_name_input.link(
                (key),
                callbacks={"value": self.change_band_name},
            )
            band_freq_input = pn.widgets.ArrayInput(value=np.array(value))
            band_freq_input.link(
                (key),
                callbacks={"value": self.change_freq_bands},
            )
            pane.append(
                pn.Row(
                    band_name_input,
                    band_freq_input,
                    remove_btn,
                )
            )
        add_band = pn.widgets.Button(name="Add", button_type="primary")
        add_band.link(
            None,
            callbacks={"value": self.add_band},
        )
        pane.append(pn.Row(add_band))
        self.band_panel.objects = [pane]

    def change_freq_bands(self, key, target):
        if len(target.new) == 2:
            self.freq_bands[key] = list(target.new)
        self.show_freq_bands()

    def change_band_name(self, key, target):
        self.freq_bands[target.new] = self.freq_bands.pop(key)
        self.show_freq_bands()

    def change_phase_name(self, target, event):
        self.subj_time_dict[target[0]][target[1]].rename(
            {target[2]: event.new}, inplace=True
        )
        self.dict_to_column()

    def remove_band(self, key, target):
        self.freq_bands.pop(key)
        self.show_freq_bands()

    def add_band(self, _, target):
        new_name = "new"
        i = 0
        while new_name in self.freq_bands.keys():
            i += 1
            new_name = "new " + str(i)
        self.freq_bands[new_name] = [0, 0]
        self.show_freq_bands()

    @param.output(
        ("freq_bands", param.Dynamic),
        ("data", param.Dynamic),
        ("sampling_rate", param.Dynamic),
        ("subj_time_dict", param.Dynamic),
        ("selected_signal", param.Dynamic),
    )
    def output(self):
        return (
            self.freq_bands,
            self.data,
            self.sampling_rate,
            self.subj_time_dict,
            self.selected_signal,
        )

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
        # self.step = 8
        # self.set_progress_value()
        if self.text == "":
            f = open("../assets/Markdown/ChangeFreqBands.md", "r")
            fileString = f.read()
            self.text = fileString
        self.show_freq_bands()
        return pn.Column(
            # pn.Row(self.get_step_static_text()),
            # pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            # pn.Row(self.yes_btn, self.no_btn),
            self.band_panel,
        )
