import pandas
import pandas as pd
import panel as pn
import param
import biopsykit as bp
import re

# TODO: Custom Filter Function
class SuggestQuestionnaireScores(param.Parameterized):
    text = ""
    data = param.Dynamic(default=None)
    dict_scores = {}
    accordion = pn.Accordion(sizing_mode="stretch_width")
    select_questionnaire = pn.widgets.Select(
        name="Choose Questionnaire:",
        options=list(bp.questionnaires.utils.get_supported_questionnaires().keys()),
    )
    add_questionnaire_btn = pn.widgets.Button(
        name="Add Questionnaire", button_type="primary", align="end"
    )

    def init_dict_scores(self):
        if bool(self.dict_scores):
            return
        for name in bp.questionnaires.utils.get_supported_questionnaires().keys():
            questionnaire_cols = self.data.filter(regex=f"(?i)({name})").columns
            # data_filt, cols = bp.questionnaires.utils.find_cols(
            #     data=self.data, regex_str=f"(?i)({name})"
            # )
            col_sum = 0
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
        # if any("post" in x.lower() for x in list_col):
        #     self.dict_scores[name + "-post"] = pandas.Index(data=l)
        #     col_sum += len(self.dict_scores[name + "-post"])
        # if any("pre" in x.lower() for x in questionnaire_cols):
        #     self.dict_scores[name + "-pre"] = pandas.Index(data=l)
        #     col_sum += len(self.dict_scores[name + "-pre"])
        # # Wenn col_sum != len(cols) müssen noch weiter cols hinzugefügt werden
        # if not data_filt.empty:
        #     self.dict_scores[name] = cols

    @staticmethod
    def edit_mode_on(target, event):
        target.disabled = (event.new % 2) == 0

    def change_columns(self, target, event):
        df = self.data[event.new]
        cols = df.columns
        self.dict_scores[target] = cols

    def get_accordion_item(self, questionnaire_key) -> pn.Column:
        col = pn.Column(name=questionnaire_key)
        height = min(400, 100 + len(self.data.columns.tolist()) * 5)
        edit_btn = pn.widgets.Button(name="Edit", button_type="primary")
        remove_btn = pn.widgets.Button(
            name="Remove", button_type="light", align="end", disabled=True
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
        self.add_questionnaire_btn.link(
            None,
            callbacks={"value": self.add_questionnaire},
        )
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

    def remove_questionnaire(self, target, _):
        index = [x.name for x in self.accordion.objects].index(target)
        self.accordion.pop(index)
        self.dict_scores.pop(target)
        pn.state.notifications.warning(f"Questionnaire {target} was removed")

    def change_reg_ex(self, target, event):
        pass

    def change_ends_with(self, target, event):
        pass

    def change_starts_with(self, target, event):
        pass

    def add_questionnaire(self, target, event):
        questionnaire = self.select_questionnaire.value
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

    @param.output(("data", param.Dynamic), ("dict_scores", param.Dict))
    def output(self):
        return (
            self.data,
            self.dict_scores,
        )

    def panel(self):
        self.accordion = pn.Accordion(sizing_mode="stretch_width")
        if self.text == "":
            f = open("../assets/Markdown/FillScoreDict.md", "r")
            fileString = f.read()
            self.text = fileString
        self.init_dict_scores()
        return pn.Column(pn.pane.Markdown(self.text), self.show_dict_scores())
