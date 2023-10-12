import param

from src.Physiological.custom_components import PipelineHeader
from src.Sleep.SLEEP_CONSTANTS import MAX_STEPS


class SleepBase(param.Parameterized):
    selected_device = param.String(default="")
    step = param.Integer(default=1)
    selected_parameters = {}
    data = param.Dynamic(default=None)

    def __init__(self, **params):
        header_text = params.pop("HEADER_TEXT") if "HEADER_TEXT" in params else ""
        self.header = PipelineHeader(1, MAX_STEPS, header_text)
        super().__init__(**params)

    def update_step(self, step: int | param.Integer):
        self.step = step
        self.header.update_step(step)

    def update_text(self, text: str | param.String):
        self.header.update_text(text)

    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
    )
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
        )
