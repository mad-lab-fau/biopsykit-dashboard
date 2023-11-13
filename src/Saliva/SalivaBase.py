import param

from src.Physiological.custom_components import PipelineHeader
from src.Saliva.SALIVA_CONSTANTS import SALIVA_MAX_STEPS


class SalivaBase(param.Parameterized):
    condition_list = param.Dynamic(default=None)
    data = param.Dynamic()
    format = param.String(default=None)
    saliva_type = param.String(default="")
    sample_id = param.String(default=None)
    sample_times = param.Dynamic(default=None)
    step = param.Integer(default=1)

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, SALIVA_MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    @param.output(
        ("condition_list", param.Dynamic),
        ("format", param.String),
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.List),
    )
    def output(self):
        return (
            self.condition_list,
            self.format,
            self.data,
            self.saliva_type,
            self.sample_times,
        )
