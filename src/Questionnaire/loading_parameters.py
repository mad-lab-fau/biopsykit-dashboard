import param
import panel as pn


class AskToSetLoadingParameters(param.Parameterized):
    text = ""
    next = param.Selector(
        default="Upload Questionnaire Data",
        objects=["Upload Questionnaire Data", "Set Loading Parameters"],
    )
    ready = param.Boolean(default=False)
    default_btn = pn.widgets.Button(name="Default")
    set_parameters_manually = pn.widgets.Button(
        background="#d5433e", name="Set Loading Parameters", button_type="success"
    )

    def click_default(self, _):
        self.next = "Upload Questionnaire Data"
        self.ready = True

    def click_set_parameters(self, _):
        self.next = "Set Loading Parameters"
        self.ready = True

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/AskToSetLoadingParameters.md", "r")
            fileString = f.read()
            self.text = fileString
        self.set_parameters_manually.on_click(self.click_set_parameters)
        self.default_btn.on_click(self.click_default)
        return pn.Column(
            pn.pane.Markdown(self.text),
            pn.Row(self.default_btn, self.set_parameters_manually),
        )


class SetLoadingParametersExpert(param.Parameterized):
    text = ""
    subject_col = pn.widgets.TextInput(
        name="subject_col",
        value=None,
        placeholder="Enter the name of your subject column",
    )
    condition_col = pn.widgets.TextInput(
        name="condition_col",
        value=None,
        placeholder="Enter the name of your condition column",
    )
    additional_index_cols = pn.widgets.ArrayInput(
        name="additional_index_cols", value=None
    )
    replace_missing_vals = pn.widgets.Checkbox(name="replace_missing_vals", value=True)
    remove_nan_rows = pn.widgets.Checkbox(name="remove_nan_rows", value=True)
    sheet_name = pn.widgets.TextInput(
        name="sheet_name",
        value="0",
        placeholder="Enter the name or index of the sheet",
    )

    @param.output(
        ("subject_col", param.String),
        ("condition_col", param.String),
        ("additional_index_cols", param.Dynamic),
        ("replace_missing_vals", param.Boolean),
        ("remove_nan_rows", param.Boolean),
        ("sheet_name", param.Dynamic),
    )
    def output(self):
        sheet_name = self.sheet_name.value
        if sheet_name.isnumeric():
            sheet_name = int(sheet_name)
        return (
            self.subject_col.value,
            self.condition_col.value,
            self.additional_index_cols.value,
            self.replace_missing_vals.value,
            self.remove_nan_rows.value,
            sheet_name,
        )

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/LoadQuestionnaireData.md", "r")
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.subject_col,
            self.condition_col,
            self.additional_index_cols,
            self.replace_missing_vals,
            self.remove_nan_rows,
            self.sheet_name,
        )
