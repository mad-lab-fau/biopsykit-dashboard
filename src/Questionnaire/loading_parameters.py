import param
import panel as pn

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import (
    ASK_TO_SET_LOADING_PARAMETERS_TEXT,
    LOAD_QUESTIONNAIRE_DATA_TEXT,
)
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class AskToSetLoadingParameters(QuestionnaireBase):
    next = param.Selector(
        default="Upload Questionnaire Data",
        objects=["Upload Questionnaire Data", "Set Loading Parameters"],
    )
    ready = param.Boolean(default=False)
    default_btn = pn.widgets.Button(name="Default")
    set_parameters_manually = pn.widgets.Button(
        name="Set Loading Parameters",
        button_type="primary",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_SET_LOADING_PARAMETERS_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(ASK_TO_SET_LOADING_PARAMETERS_TEXT)
        self.set_parameters_manually.on_click(self.click_set_parameters)
        self.default_btn.on_click(self.click_default)
        self._view = pn.Column(
            self.header,
            pn.Row(self.default_btn, self.set_parameters_manually),
        )

    def click_default(self, _):
        self.next = "Upload Questionnaire Data"
        self.ready = True

    def click_set_parameters(self, _):
        self.next = "Set Loading Parameters"
        self.ready = True

    def panel(self):
        return self._view


class SetLoadingParametersManually(QuestionnaireBase):
    select_subject_col = pn.widgets.TextInput(
        name="subject_col",
        value=None,
        placeholder="Enter the name of your subject column",
    )
    set_condition_col = pn.widgets.TextInput(
        name="condition_col",
        value=None,
        placeholder="Enter the name of your condition column",
    )
    set_additional_index_cols = pn.widgets.ArrayInput(
        name="additional_index_cols", value=None
    )
    check_replace_missing_vals = pn.widgets.Checkbox(
        name="replace_missing_vals", value=True
    )
    check_remove_nan_rows = pn.widgets.Checkbox(name="remove_nan_rows", value=True)
    set_sheet_name = pn.widgets.TextInput(
        name="sheet_name",
        value="0",
        placeholder="Enter the name or index of the sheet",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOAD_QUESTIONNAIRE_DATA_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(LOAD_QUESTIONNAIRE_DATA_TEXT)
        self.select_subject_col.link(
            self, callbacks={"value": self.selected_subject_col_changed}
        )
        self.set_condition_col.link(
            self, callbacks={"value": self.condition_col_changed}
        )
        self.set_additional_index_cols.link(
            self, callbacks={"value": self.additional_index_cols_changed}
        )
        self.check_replace_missing_vals.link(
            self, callbacks={"value": self.check_replace_missing_vals_changed}
        )
        self.check_remove_nan_rows.link(
            self, callbacks={"value": self.remove_nan_rows_changed}
        )
        self.set_sheet_name.link(self, callbacks={"value": self.sheet_name_changed})
        self._view = pn.Column(
            self.header,
            self.select_subject_col,
            self.set_condition_col,
            self.set_additional_index_cols,
            self.check_replace_missing_vals,
            self.check_remove_nan_rows,
            self.set_sheet_name,
        )

    def sheet_name_changed(self, _, event):
        sheet_name = event.new
        if sheet_name.isnumeric():
            self.sheet_name = int(sheet_name)
        else:
            self.sheet_name = event.new

    def remove_nan_rows_changed(self, _, event):
        self.remove_nan_rows = event.new

    def check_replace_missing_vals_changed(self, _, event):
        self.replace_missing_vals = event.new

    def additional_index_cols_changed(self, _, event):
        self.additional_index_cols = event.new

    def condition_col_changed(self, _, event):
        self.condition_col = event.new

    def selected_subject_col_changed(self, _, event):
        self.subject_col = event.new

    def panel(self):
        return self._view
