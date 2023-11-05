import pandas as pd
import panel as pn
import biopsykit as bp

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import SUGGEST_QUESTIONNAIRE_SCORES_TEXT
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class SuggestQuestionnaireScores(QuestionnaireBase):
    accordion = pn.Accordion(sizing_mode="stretch_width")
    select_questionnaire = pn.widgets.Select(
        name="Choose Questionnaire:",
        options=list(bp.questionnaires.utils.get_supported_questionnaires().keys()),
    )
    add_questionnaire_btn = pn.widgets.Button(
        name="Add Questionnaire", button_type="primary", align="end"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = SUGGEST_QUESTIONNAIRE_SCORES_TEXT
        super().__init__(**params)
        self.add_questionnaire_btn.link(
            self.select_questionnaire.value,
            callbacks={"clicks": self.add_questionnaire},
        )
        self.update_step(3)
        self.update_text(SUGGEST_QUESTIONNAIRE_SCORES_TEXT)

    def init_dict_scores(self):
        if bool(self.dict_scores):
            return
        for name in bp.questionnaires.utils.get_supported_questionnaires().keys():
            questionnaire_cols = self.data.filter(regex=f"(?i)({name})").columns
            list_col = list(questionnaire_cols)
            cols = {"-pre": [], "-post": [], "": []}
            for c in list_col:
                if "pre" in c.lower():
                    cols["-pre"].append(c)
                elif "post" in c.lower():
                    cols["-post"].append(c)
                else:
                    cols[""].append(c)
            for key in cols.keys():
                if len(cols[key]) != 0:
                    self.dict_scores[name + key] = pd.Index(data=cols[key])

    @staticmethod
    def edit_mode_on(target, event):
        target.disabled = (event.new % 2) == 0

    def change_columns(self, target, event):
        df = self.data[event.new]
        cols = df.columns
        self.dict_scores[target] = cols

    def get_accordion_item(self, questionnaire_key) -> pn.Column:
        col = pn.Column(name=questionnaire_key)
        if self.data is None:
            return col
        height = min(400, 100 + len(self.data.columns.tolist()) * 5)
        edit_btn = pn.widgets.Button(name="Edit", button_type="primary")
        remove_btn = pn.widgets.Button(
            name="Remove",
            align="end",
            disabled=True,
            button_type="danger",
        )
        remove_btn.link(
            questionnaire_key,
            callbacks={"value": self.remove_questionnaire},
        )
        rename_field = pn.widgets.TextInput(name="Rename", disabled=True)
        rename_field.link(
            questionnaire_key,
            callbacks={"value": self.rename_questionnaire},
        )
        edit_btn.link(remove_btn, callbacks={"clicks": self.edit_mode_on})
        edit_btn.link(rename_field, callbacks={"clicks": self.edit_mode_on})
        col.append(edit_btn)
        col.append(remove_btn)
        col.append(rename_field)
        col.append(pn.layout.Divider())
        cross_selector = pn.widgets.CrossSelector(
            name=questionnaire_key,
            value=self.dict_scores[questionnaire_key].tolist(),
            options=self.data.columns.tolist(),
            height=height,
        )
        cross_selector.link(questionnaire_key, callbacks={"value": self.change_columns})
        col.append(cross_selector)
        return col

    def show_dict_scores(self):
        col = pn.Column()
        if self.dict_scores is None or len(self.dict_scores) == 0:
            return col
        row = pn.Row()
        row.append(self.select_questionnaire)
        row.append(self.add_questionnaire_btn)
        gridBox = pn.GridBox(ncols=1)
        for questionnaire in self.dict_scores.keys():
            acc = self.get_accordion_item(questionnaire)
            self.accordion.append(acc)
        gridBox.append(self.accordion)
        col.append(gridBox)
        col.append(pn.layout.Divider())
        col.append(row)
        return col

    def remove_questionnaire(self, questionnaire_to_remove: str, _):
        try:
            index = [x.name for x in self.accordion.objects].index(
                questionnaire_to_remove
            )
            self.accordion.pop(index)
            self.dict_scores.pop(questionnaire_to_remove)
            pn.state.notifications.warning(
                f"Questionnaire {questionnaire_to_remove} was removed"
            )
        except ValueError as e:
            pn.state.notifications.error(
                f"Questionnaire {questionnaire_to_remove} could not be removed: {e}"
            )

    def add_questionnaire(self, selected_questionnaire, _):
        questionnaire = selected_questionnaire
        if questionnaire is None or questionnaire == "" or self.data is None:
            pn.state.notifications.error("No Questionnaire selected")
            return
        i = 0
        while questionnaire in self.dict_scores.keys():
            questionnaire = self.select_questionnaire.value + f"-New{i}"
            i += 1
        self.dict_scores[questionnaire] = bp.questionnaires.utils.find_cols(
            data=self.data, contains=questionnaire
        )[1]
        self.accordion.append(self.get_accordion_item(questionnaire))

    def rename_questionnaire(self, target, event):
        old_name, new_name = target, event.new
        score = new_name
        if "-" in score:
            score_split = score.split("-")
            score = score_split[0]
        if score not in list(
            bp.questionnaires.utils.get_supported_questionnaires().keys()
        ):
            pn.state.notifications.error(f"Questionnaire: {score} not supported")
            return
        index = [x.name for x in self.accordion.objects].index(old_name)
        self.dict_scores[new_name] = self.dict_scores.pop(old_name)
        a = self.get_accordion_item(new_name)
        self.accordion.__setitem__(index, a)
        pn.state.notifications.success(
            f"Questionnaire {old_name} was renamed to {new_name}"
        )

    def panel(self):
        self.init_dict_scores()
        return pn.Column(self.header, self.show_dict_scores())
