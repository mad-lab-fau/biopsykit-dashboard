import numpy as np
import panel as pn
import param

from src.Physiological.PHYSIOLOGICAL_CONSTANTS import SELECT_FREQUENCY_TEXT
from src.Physiological.PhysiologicalBase import PhysiologicalBase


class FrequencyBands(PhysiologicalBase):
    text = ""
    band_panel = pn.Column()
    freq_bands = {
        "theta": [4, 8],
        "alpha": [8, 13],
        "beta": [13, 30],
        "gamma": [30, 44],
    }

    def __init__(self, **params):
        params["HEADER_TEXT"] = SELECT_FREQUENCY_TEXT
        super().__init__(**params)
        self.update_step(9)
        pane = pn.Column(
            self.header,
            self.band_panel,
        )
        self._view = pane

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
        self.subject_time_dict[target[0]][target[1]].rename(
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

    def panel(self):
        return self._view
