import panel as pn
import param
import biopsykit as bp
import numpy as np
import pandas as pd


class AskToCropScale(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    crop_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Crop Scales",
        objects=["Crop Scales", "Show Results"],
    )

    def skip_crop(self, target, event):
        self.next_page = "Show Results"
        self.ready = True

    def crop_scales(self, target, event):
        self.next_page = "Crop Scales"
        self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
    )
    def output(self):
        return (self.data, self.dict_scores, self.data_scores, self.data_scaled)

    def panel(self):
        text = "# Would you like to crop the scale(s) of your data?"
        self.skip_btn.link(None, callbacks={"clicks": self.skip_crop})
        self.crop_btn.link(None, callbacks={"clicks": self.crop_scales})
        row = pn.Row()
        row.append(self.crop_btn)
        row.append(self.skip_btn)
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        col.append(row)
        return col


class CropScales(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    crop_btn = pn.widgets.Button(name="Crop Scale", button_type="primary")
    questionnaire_selector = pn.widgets.Select(name="Questionnaire")
    set_nan_checkbox = pn.widgets.Checkbox(
        name="Set NaN values", visible=False, value=False
    )
    questionnaire_stat_values_df = pn.widgets.DataFrame(
        name="Statistical Values",
        visible=False,
        autosize_mode="force_fit",
        height=300,
    )
    score_range_arrayInput = pn.widgets.ArrayInput(name="Score Range")

    # Target[0] = CheckBox Target[1] = DF Target[2]=ArrayInput event.new = questionnaire
    def selection_changed(self, target, event):
        if event.new == "":
            target[0].visible = False
            target[1].visible = False
            target[2].visible = False
            target[2].value = None
            self.crop_btn.visible = False
            self.set_nan_checkbox.value = False
            return
        questionnaire_data = self.data
        if self.data_scaled is not None:
            questionnaire_data = self.data_scaled
        questionnaire_data = questionnaire_data[self.dict_scores[event.new].to_list()]
        target[0].visible = bool(questionnaire_data.isnull().values.any())
        target[2].visible = True
        target[2].value = np.array(
            [questionnaire_data.to_numpy().min(), questionnaire_data.to_numpy().max()]
        )
        target[1].value = questionnaire_data.describe().transpose()
        target[1].visible = True
        self.crop_btn.visible = True

    def crop_data(self, target, event):
        if self.questionnaire_selector.value is None:
            return
        key = self.questionnaire_selector.value
        set_nan = self.set_nan_checkbox.value
        cols = self.dict_scores[key].to_list()
        score_range = self.score_range_arrayInput.value
        if len(score_range) != 2:
            pn.state.notifications.error(
                "Score Range has the false length. It must be 2"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data
        try:
            self.data_scaled[cols] = bp.questionnaires.utils.crop_scale(
                data=self.data_scaled[cols], score_range=score_range, set_nan=set_nan
            )
            self.questionnaire_stat_values_df.value = (
                self.data_scaled[cols].describe().transpose()
            )
            pn.state.notifications.success(
                f"Successfully cropped the data of questionnaire {key}"
            )
        except Exception as e:
            pn.state.notifications.error(f"Error while cropping the data: {e}")

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
    )
    def output(self):
        return (self.data, self.dict_scores, self.data_scores, self.data_scaled)

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        self.crop_btn.visible = False
        self.questionnaire_selector.link(
            (
                self.set_nan_checkbox,
                self.questionnaire_stat_values_df,
                self.score_range_arrayInput,
            ),
            callbacks={"value": self.selection_changed},
        )
        self.crop_btn.link(None, callbacks={"clicks": self.crop_data})
        text = (
            "# Crop scales"
            + "\n"
            + "Crop questionnaire scales, i.e., set values out of range to specific minimum and maximum values or to NaN."
        )
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        col.append(self.questionnaire_selector)
        col.append(self.score_range_arrayInput)
        col.append(self.set_nan_checkbox)
        col.append(self.questionnaire_stat_values_df)
        col.append(self.crop_btn)
        return col
