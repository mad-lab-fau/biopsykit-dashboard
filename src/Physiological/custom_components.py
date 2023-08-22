import param
from panel.viewable import Viewer
import panel as pn


class PipelineHeader(Viewer):

    textField = param.String()
    step = param.Integer(default=1)
    max_step = param.Integer(default=100)

    def __init__(
        self,
        step: int | param.Integer,
        max_step: int | param.Integer,
        text: str | param.String,
        **params
    ):
        self._progress = pn.indicators.Progress(
            name="Progress",
            height=20,
            sizing_mode="stretch_width",
            max=step,
            value=max_step,
        )
        self._step_text = pn.widgets.StaticText(
            name="Progress", value="Step " + str(step) + " of " + str(max_step)
        )
        self._text = pn.pane.Markdown(text)
        super().__init__(**params)
        self._layout = pn.Column(
            pn.Row(self._step_text),
            pn.Row(self._progress),
            pn.pane.Markdown(text),
        )

    def update_step(self, step: int):
        self.step = step
        self._step_text.value = "Step " + str(step) + " of " + str(self.max_step)
        self._progress.value = step

    def update_text(self, text: str):
        self._text.object = text

    def __panel__(self):
        return self._layout


class Timestamp(Viewer):

    value = param.Tuple(doc="First value is the name the second the timestamp")
    remove = False
    name = param.String()

    def __init__(self, **params):
        self._timestamp_name = pn.widgets.StaticText()
        self._timestamp_datetime = pn.widgets.DatetimePicker()
        self._timestamp_remove = pn.widgets.Button(name="Remove", button_type="primary")
        super().__init__(**params)
        self._layout = pn.Row(
            self._timestamp_name, self._timestamp_datetime, self._timestamp_remove
        )
        self._sync_widgets()
        # self._timestamp_remove.on_click(self.)

    def __panel__(self):
        return self._layout

    @param.depends("_timestamp_remove.value", watch=True)
    def remove_btn_click(self):
        self.remove = True

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        self._timestamp_name.value = self.value[0]
        self._timestamp_datetime.value = self.value[1]

    @param.depends("_timestamp_datetime.value", watch=True)
    def _sync_params(self):
        self.value = (self._timestamp_name.value, self._timestamp_datetime.value)


class TimestampList(Viewer):

    value = param.List(doc="List of Tuples (str, DateTime)")
    col = pn.Column()
    timestamps = []
    name = param.String()

    def __init__(self, **params):
        super().__init__(**params)
        self._layout = self.col
        self._sync_widgets()

    @param.depends("value", watch=True)
    def _sync_widgets(self):
        for nt in self.value:
            ts = Timestamp(name=nt[0], value=(nt[0], nt[1]))
            ts._timestamp_remove.on_click(self.remove_btn_click)
            self.col.append(ts)

    def __panel__(self):
        self._layout = self.col
        return self._layout

    def remove_btn_click(self, event):
        # Check all Items in
        print("In TimestampList")
        print(event)
