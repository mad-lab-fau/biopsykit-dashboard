import matplotlib
import param
import panel as pn
import biopsykit as bp
from fau_colors import cmaps
import seaborn as sns

from src.Questionnaire.dataframe_styler import make_pretty


class CheckSelectedQuestionnaires(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    text = ""
    check_btn = pn.widgets.Button(
        name="Check Questionnaires", sizing_mode="stretch_width"
    )
    accordion = pn.Accordion(sizing_mode="stretch_width")
    col = pn.Column(sizing_mode="stretch_width")

    def init_questionnaire_panel(self, visible: bool) -> pn.Accordion:
        acc = pn.Accordion(sizing_mode="stretch_width", visible=visible)
        for questionnaire in self.dict_scores.keys():
            df = self.data[list(self.dict_scores[questionnaire])].style.pipe(
                make_pretty
            )
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

    def check_questionnaires(self, _, event):
        acc = self.init_questionnaire_panel((event.new % 2) != 0)
        self.col.__setitem__(2, acc)

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
    )
    def output(self):
        return (
            self.data,
            self.dict_scores,
        )

    def panel(self):
        if len(self.col.objects) > 0:
            return self.col
        if self.text == "":
            f = open("../assets/Markdown/CheckSelectedQuestionnaires.md", "r")
            fileString = f.read()
            self.text = fileString
        self.check_btn.link(None, callbacks={"clicks": self.check_questionnaires})
        self.col.append(pn.pane.Markdown(self.text))
        self.col.append(self.check_btn)
        self.col.append(self.init_questionnaire_panel(False))
        return self.col
