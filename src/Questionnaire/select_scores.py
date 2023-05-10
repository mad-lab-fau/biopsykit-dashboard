import pandas as pd
import panel as pn
import param
import biopsykit as bp

# TODO: Rename Questionnaire, Linking
class SuggestQuestionnaireScores(param.Parameterized):
    text = ""
    data = param.Dynamic(default=None)
    dict_scores = {}

    def init_dict_scores(self):
        for name in bp.questionnaires.utils.get_supported_questionnaires().keys():
            data_filt, cols = bp.questionnaires.utils.find_cols(
                data=self.data, regex_str=f"(?i)({name})"
            )
            if not data_filt.empty:
                self.dict_scores[name] = cols

    def show_dict_scores(self):
        col = pn.Column()
        add_questionnaire_btn = pn.widgets.Button(
            name="Add Questionnaire", button_type="primary"
        )
        add_questionnaire_btn.link(
            None,
            callbacks={"value": self.add_questionnaire},
        )
        col.append(add_questionnaire_btn)
        gridBox = pn.GridBox(ncols=2)
        for test in self.dict_scores:
            w = self.get_widgetBox(test)

            gridBox.append(w)
        col.append(gridBox)
        return col

    def get_widgetbox(self, questionnaire_key) -> pn.WidgetBox:
        starts_with = pn.widgets.TextInput(name="Starts With", value="")
        starts_with.link(
            questionnaire_key,
            callbacks={"value": self.change_starts_with},
        )
        ends_with = pn.widgets.TextInput(name="Ends With", value="")
        regex = pn.widgets.TextInput(name="RegEx", value=f"(?i)({questionnaire_key})")
        remove_btn = pn.widgets.Button(name="Remove", button_type="primary")
        r = pn.Row()
        r.append(f"# {questionnaire_key.upper()}")
        r.append(pn.widgets.Button(name="Rename", button_type="light", align="center"))
        w = pn.WidgetBox(r, starts_with, ends_with, regex, remove_btn)
        return w

    def remove_questionnaire(self, target, event):
        pass

    def change_reg_ex(self, target, event):
        pass

    def change_ends_with(self, target, event):
        pass

    def change_starts_with(self, target, event):
        # data_filt, cols = bp.questionnaires.utils.find_cols(
        #     data=self.data, regex_str=f"(?i)({target})"
        # )
        pass

    def add_questionnaire(self, target, event):
        pass

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/FillScoreDict.md", "r")
            fileString = f.read()
            self.text = fileString
        self.init_dict_scores()
        return pn.Column(pn.pane.Markdown(self.text), self.show_dict_scores())


class SelectScores(param.Parameterized):
    text = ""

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/FillScoreDict.md", "r")
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.scores,
        )
