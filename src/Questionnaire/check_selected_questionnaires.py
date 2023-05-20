import matplotlib
import param
import panel as pn
import biopsykit as bp
from fau_colors import cmaps
import seaborn as sns


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
            acc.append(
                (
                    questionnaire,
                    pn.widgets.DataFrame(
                        value=self.data[list(self.dict_scores[questionnaire])].head(),
                        autosize_mode="fit_columns",
                    ),
                )
            )
            test = self.data[list(self.dict_scores[questionnaire])].style.pipe(
                self.make_pretty
            )
            cell_hover = {  # for row hover use <tr> instead of <td>
                "selector": "td:hover",
                "props": [("background-color", "#ffffb3")],
            }
            test.set_table_styles([cell_hover])
            test.set_sticky(axis="index")
            a = test.to_html()
            html = pn.pane.HTML(a)
            acc.append(html)
            # acc.append(pn.pane.HTML(a))
        return acc

    @staticmethod
    def make_pretty(styler):
        styler.set_caption("Questionnaire")
        # styler.format_index(lambda v: v.strftime("%A"))
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
            "", cmaps.faculties_light
        )
        styler.background_gradient(axis=None, vmin=1, vmax=5, cmap=cmap)
        return styler

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
