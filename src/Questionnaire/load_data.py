from io import StringIO

import param
import panel as pn

from src.utils import load_questionnaire_data


class LoadQuestionnaireData(param.Parameterized):
    text = ""
    ready = param.Boolean(default=False)
    step = 1
    max_steps = 10
    progress = pn.indicators.Progress(
        name="Progress",
        height=20,
        sizing_mode="stretch_width",
    )
    file_input = pn.widgets.FileInput(
        styles={"background": "whitesmoke"},
        multiple=False,
        accept=".csv,.bin,.xls,.xlsx,.zip",
    )
    data = param.Dynamic(default=None)
    subject_col = param.String(default=None)
    condition_col = param.String(default=None)
    additional_index_cols = param.Dynamic(default=None)
    replace_missing_vals = param.Boolean(default=True)
    remove_nan_rows = param.Boolean(default=True)
    sheet_name = param.Dynamic(default=0)

    def parse_file_input(self, _):
        try:
            if ".zip" in self.file_input.filename:
                pn.state.notifications.error("Not yet implemented")
                self.ready = False
            else:
                self.data = load_questionnaire_data(
                    file=self.file_input.value,
                    file_name=self.file_input.filename,
                    subject_col=self.subject_col,
                    condition_col=self.condition_col,
                    additional_index_cols=self.additional_index_cols,
                    replace_missing_vals=self.replace_missing_vals,
                    remove_nan_rows=self.remove_nan_rows,
                    sheet_name=self.sheet_name,
                )
                self.ready = True
                pn.state.notifications.success("Files uploaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    @param.output(
        ("data", param.String),
    )
    def output(self):
        return (self.data,)

    def get_step_static_text(self):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(self.step) + " of " + str(self.max_steps),
        )

    def set_progress_value(self):
        self.progress.value = int((self.step / self.max_steps) * 100)

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/LoadQuestionnaireData.md", "r")
            fileString = f.read()
            self.text = fileString
        self.set_progress_value()
        pn.bind(self.parse_file_input, self.file_input.param.value, watch=True)
        return pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            self.file_input,
        )
