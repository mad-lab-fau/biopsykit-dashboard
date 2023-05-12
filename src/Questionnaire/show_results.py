import param
import panel as pn


class ShowResults(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    text = "# Show Results"

    def panel(self):
        return pn.Column(
            pn.pane.Markdown(self.text),
            pn.widgets.DataFrame(
                self.data_scores.head(),
                autosize_mode="fit_columns",
                sizing_mode="stretch_width",
            ),
        )
