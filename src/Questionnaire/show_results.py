import param
import panel as pn
import biopsykit as bp
import re
from src.Questionnaire.dataframe_styler import make_pretty


class ShowResults(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    results = param.Dynamic()
    text = "# Show Results"
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Ask to change format"],
    )

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
        ("results", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.dict_scores,
            self.data_scores,
            self.data_scaled,
            self.results,
        )

    def showQuestionnaireResults(self) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width")
        supported_questionnaires = (
            bp.questionnaires.utils.get_supported_questionnaires()
        )
        for questionnaire in supported_questionnaires:
            questionnaire_results = self.results.filter(like=questionnaire.upper())
            if questionnaire_results.empty:
                continue
            df = questionnaire_results.style.pipe(make_pretty)
            cell_hover = {
                "selector": "td:hover",
                "props": [("background-color", "#040fe0")],
            }
            df.set_table_styles([cell_hover])
            df.set_sticky(axis="index")
            a = df.to_html()
            html = pn.pane.HTML(a)
            acc.append(
                (
                    questionnaire,
                    html,
                )
            )
        return acc

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        self.results = bp.questionnaires.utils.compute_scores(
            data=self.data_scaled, quest_dict=self.dict_scores
        )
        if all("_" in cols for cols in self.results.columns.to_list()):
            self.next_page = "Ask to change format"
        col = pn.Column()
        col.append(pn.pane.Markdown(self.text))
        col.append(self.showQuestionnaireResults())
        return col
        # return pn.Column(
        #     pn.pane.Markdown(self.text),
        #     pn.widgets.DataFrame(
        #         self.results.head(),
        #         autosize_mode="fit_columns",
        #         sizing_mode="stretch_width",
        #     ),
        # )
