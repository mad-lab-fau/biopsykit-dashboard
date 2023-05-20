import numpy as np
import panel as pn
import param
import biopsykit as bp


class AskToInvertScores(param.Parameterized):
    text = "# Do you want to invert the scores of selected column(s) ?"
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Invert Scores",
        objects=["Invert Scores", "Ask to change format", "Show Results"],
    )
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    invert_scores_btn = pn.widgets.Button(name="Yes")
    data = param.Dynamic()
    data_scaled = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()

    def skip_inverting(self, target, event):
        if any(
            all("_" in cols for cols in self.dict_scores[x].to_list())
            for x in self.dict_scores.keys()
        ):
            self.next_page = "Ask to change format"
        else:
            self.next_page = "Show Results"
        self.ready = True

    def invert_scores(self, target, event):
        self.next_page = "Invert Scores"
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
        self.skip_btn.link(None, callbacks={"clicks": self.skip_inverting})
        self.invert_scores_btn.link(None, callbacks={"clicks": self.invert_scores})
        col = pn.Column()
        col.append(pn.pane.Markdown(self.text))
        row = pn.Row()
        row.append(self.invert_scores_btn)
        row.append(self.skip_btn)
        col.append(row)
        return col


class InvertScores(param.Parameterized):
    text = "# Invert Scores"
    data = param.Dynamic()
    data_scaled = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    questionnaire_selector = pn.widgets.Select(name="Select Questionnaire")
    select_all_checkbox = pn.widgets.Checkbox(
        name="Select All", value=False, visible=False
    )
    column_cross_selector = pn.widgets.CrossSelector(
        name="Select Column(s)", visible=False
    )
    invert_scores_btn = pn.widgets.Button(name="Invert the scores", visible=False)
    score_range_array_input = pn.widgets.ArrayInput(
        name="Score Range", value=np.array([0, 0]), visible=False
    )

    def questionnaire_changed(self, _, event):
        questionnaire = event.new
        if questionnaire == "":
            self.select_all_checkbox.visible = False
            self.column_cross_selector.visible = False
            self.invert_scores_btn.visible = False
            self.score_range_array_input.visible = False
            return
        self.select_all_checkbox.value = False
        self.select_all_checkbox.visible = True
        self.column_cross_selector.options = self.dict_scores[questionnaire].to_list()
        self.column_cross_selector.height = min(
            400, 100 + len(self.data.columns.tolist()) * 5
        )
        self.column_cross_selector.visible = True
        self.score_range_array_input.value = np.array([0, 0])
        self.score_range_array_input.visible = True
        self.invert_scores_btn.visible = True

    def select_all_checked(self, target, event):
        if event.new:
            self.column_cross_selector.value = self.dict_scores[
                self.questionnaire_selector.value
            ].to_list()
        else:
            self.column_cross_selector.value = []

    def invert_scores(self, target, event):
        if len(self.column_cross_selector.value) == 0:
            pn.state.notifications.error(
                "You have to select at least one column to invert the scores"
            )
            return
        if len(self.score_range_array_input.value) != 2:
            pn.state.notifications.error(
                "You have to fill out the field Score Range in a format like : [1,2]"
            )
            return
        if self.data_scaled is None:
            self.data_scaled = self.data
        try:
            self.data_scaled = bp.questionnaires.utils.invert(
                data=self.data_scaled,
                score_range=self.score_range_array_input.value,
                cols=self.column_cross_selector.value,
            )
            pn.state.notifications.success(
                f"Successfully inverted the scores of the selected columns to the range {self.score_range_array_input.value}"
            )
        except Exception as e:
            pn.state.notifications.error(
                f"Error occured while inverting the selected columns: {e}"
            )

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
        self.questionnaire_selector.link(
            None, callbacks={"value": self.questionnaire_changed}
        )
        self.select_all_checkbox.link(
            None, callbacks={"value": self.select_all_checked}
        )
        self.invert_scores_btn.link(None, callbacks={"clicks": self.invert_scores})
        col = pn.Column()
        col.append(pn.pane.Markdown(self.text))
        col.append(self.questionnaire_selector)
        col.append(self.select_all_checkbox)
        col.append(self.column_cross_selector)
        col.append(self.invert_scores_btn)
        return col
