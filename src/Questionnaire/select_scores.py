import panel as pn
import param
import biopsykit as bp

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
            data_filt, cols = bp.questionnaires.utils.find_cols(
                data=self.data, regex_str=f"(?i)({name})"
            )
            if not data_filt.empty:
                self.dict_scores[name] = cols

    @staticmethod
    def edit_mode_on(target, event):
        target.disabled = (event.new % 2) == 0

    def change_columns(self, target, event):
        df = self.data[event.new]
        cols = df.columns
        self.dict_scores[target] = cols

    def get_accordion(self, questionnaire_key):
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
        # rename_btn = pn.widgets.Button(name="Rename", button_type="primary")
        # rename_btn.link(
        #     (questionnaire_key, rename_field.value),
        #     callbacks={"value": self.rename_questionnaire},
        # )
        # row = pn.Row()
        # row.append(rename_field)
        # row.append(rename_btn)
        # row.append(remove_btn)
        # col.append(row)
        cross_selector = pn.widgets.CrossSelector(
            name=questionnaire_key,
            value=self.dict_scores[questionnaire_key].tolist(),
            options=self.data.columns.tolist(),
            height=height,
        )
        cross_selector.link(questionnaire_key, callbacks={"value": self.change_columns})
        col.append(cross_selector)
        # starts_with = pn.widgets.TextInput(
        #     name="Beginning of the column names", value=""
        # )
        # starts_with.link(
        #     questionnaire_key,
        #     callbacks={"value": self.change_starts_with},
        # )
        # ends_with = pn.widgets.TextInput(name="Ending of the column names", value="")
        # regex = pn.widgets.TextInput(name="RegEx", value=f"(?i)({questionnaire_key})")
        # contains = pn.widgets.TextInput(
        #     name="Column names contain the substring", value=""
        # )
        # remove_btn = pn.widgets.Button(name="Remove", button_type="light")
        # apply_changes_btn = pn.widgets.Button(
        #     name="Apply Changes", button_type="primary"
        # )
        # r = pn.Row()
        # r.append(f"# {questionnaire_key.upper()}")
        # r.append(pn.widgets.Button(name="Rename", button_type="light", align="center"))
        # lastRow = pn.Row()
        # lastRow.append(apply_changes_btn)
        # lastRow.append(remove_btn)
        # col.append(starts_with)
        # col.append(ends_with)
        # col.append(contains)
        # col.append(regex)
        # col.append(
        #     pn.Accordion(
        #         (
        #             "Preview",
        #             pn.widgets.DataFrame(
        #                 self.dict_scores[questionnaire_key][0].head(),
        #                 autosize_mode="fit_columns",
        #             ),
        #         ),
        #     )
        # )
        # col.append(lastRow)

        return col

        # return (
        #     f"{questionnaire_key}",
        #     col,
        # )
        # w = pn.WidgetBox(r, starts_with, ends_with, regex, remove_btn)
        # return w

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
        for test in self.dict_scores.keys():
            acc = self.get_accordion(test)
            self.accordion.append(acc)
            # w = self.get_accordion(test)
            # gridBox.append(w)
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
        self.accordion.append(self.get_accordion(questionnaire))

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
        a = self.get_accordion(new_name)
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
