import param
import panel as pn


from src.Physiological.custom_components import PipelineHeader
from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import QUESTIONNAIRE_MAX_STEPS


class QuestionnaireBase(param.Parameterized):
    additional_index_cols = param.Dynamic(default=None)
    condition_col = param.String(default=None)
    data = param.Dynamic(default=None)
    data_in_long_format = param.Dynamic(default=None)
    data_scaled = param.Dynamic(default=None)
    data_scores = param.Dynamic()
    dict_scores = param.Dynamic(default={})
    progress = pn.indicators.Progress(
        name="Progress", height=20, sizing_mode="stretch_width"
    )
    results = param.Dynamic()
    replace_missing_vals = param.Boolean(default=False)
    remove_nan_rows = param.Boolean(default=False)
    sheet_name = param.Dynamic(default=0)
    step = param.Integer(default=1)
    subject_col = param.String(default=None)
    max_steps = QUESTIONNAIRE_MAX_STEPS

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, QUESTIONNAIRE_MAX_STEPS, header_text)
        super().__init__(**params)

    @staticmethod
    def get_progress(step) -> pn.indicators.Progress:
        return pn.indicators.Progress(
            name="Progress", height=20, sizing_mode="stretch_width", max=12, value=step
        )

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    def get_step_static_text(self, step):
        return pn.widgets.StaticText(
            name="Progress",
            value="Step " + str(step) + " of " + str(self.max_steps),
        )

    def set_progress_value(self, step):
        self.progress.value = int((step / self.max_steps) * 100)

    @param.output(
        ("subject_col", param.String),
        ("condition_col", param.String),
        ("additional_index_cols", param.Dynamic),
        ("replace_missing_vals", param.Boolean),
        ("remove_nan_rows", param.Boolean),
        ("sheet_name", param.Dynamic),
        ("data", param.Dynamic),
        ("dict_scores", param.Dynamic),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
        ("results", param.Dynamic),
        ("data_in_long_format", param.Dynamic),
    )
    def output(self):
        return (
            self.subject_col,
            self.condition_col,
            self.additional_index_cols,
            self.replace_missing_vals,
            self.remove_nan_rows,
            self.sheet_name,
            self.data,
            self.dict_scores,
            self.data_scores,
            self.data_scaled,
            self.results,
            self.data_in_long_format,
        )
