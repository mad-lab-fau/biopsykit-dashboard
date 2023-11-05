import panel as pn
import param
import biopsykit as bp
import numpy as np

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import ASK_TO_CROP_SCALE_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class AskToCropScale(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    crop_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Crop Scales",
        objects=["Crop Scales", "Ask to invert scores"],
    )

    def skip_crop(self, target, event):
        self.next_page = "Ask to invert scores"
        self.ready = True

    def crop_scales(self, target, event):
        self.next_page = "Crop Scales"
        self.ready = True

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_crop})
        self.crop_btn.link(self, callbacks={"clicks": self.crop_scales})
        self._view = pn.Column(
            self.header,
            pn.Row(self.crop_btn, self.skip_btn),
        )

    def panel(self):
        return self._view


class CropScales(QuestionnaireBase):
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

    def selection_changed(self, target, event):
        if event.new == "" or self.data is None:
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
        target[1].value = questionnaire_data.describe().transpose()[["min", "max"]]
        target[1].visible = True
        self.crop_btn.visible = True

    def crop_data(self, target, event):
        if self.questionnaire_selector.value is None:
            return
        key = self.questionnaire_selector.value
        if key is None or key not in self.dict_scores.keys():
            return
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
                data=self.data_scaled[cols],
                score_range=score_range,
                set_nan=set_nan,
                inplace=False,
            )
            self.questionnaire_stat_values_df.value = (
                self.data_scaled[cols].describe().transpose()
            )
            pn.state.notifications.success(
                f"Successfully cropped the data of questionnaire {key}"
            )
        except Exception as e:
            pn.state.notifications.error(f"Error while cropping the data: {e}")

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CROP_SCALE_TEXT
        super().__init__(**params)
        self.update_step(6)
        self.update_text(ASK_TO_CROP_SCALE_TEXT)
        self.crop_btn.link(self, callbacks={"clicks": self.crop_data})
        self.questionnaire_selector.link(
            (
                self.set_nan_checkbox,
                self.questionnaire_stat_values_df,
                self.score_range_arrayInput,
            ),
            callbacks={"value": self.selection_changed},
        )
        self._view = pn.Column(
            self.header,
            self.questionnaire_selector,
            self.score_range_arrayInput,
            self.set_nan_checkbox,
            self.questionnaire_stat_values_df,
            self.crop_btn,
        )

    def panel(self):
        self.questionnaire_selector.options = [""] + list(self.dict_scores.keys())
        self.crop_btn.visible = False
        return self._view
