import panel as pn
import param

from src.Physiological.PhysiologicalBase import PhysiologicalBase
from src.Physiological.sessions import Session


class Recordings(PhysiologicalBase):
    next_step = param.Integer()
    text = (
        "# Number of Recordings \n"
        "After you defined the kind of Sessions, in this step you will set if your data"
        "consists of a single Recording or multiple recordings.\n\n"
        "A single Recording means, that you only have one file per subject and multiple Recording"
        "is defined as two or more files per subject. \n"
    )
    recording = param.Selector(
        default="Single Recording",
        objects=["Multiple Recording", "Single Recording"],
        label="Select recording type",
    )
    next = param.Selector(
        default="Upload Files", objects=["Upload Files", "Multiple Files"]
    )

    def __init__(self):
        super().__init__()
        self.ready = True
        self._select = pn.widgets.Select.from_param(self.param.recording)
        pn.bind(self.chg, self._select.value)

    @param.depends("recording", watch=True)
    def chg(self):
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    @param.output(
        ("selected_session", param.Dynamic),
        ("selected_signal", param.String),
        ("progress_step", param.Integer),
        ("recordings", param.String),
    )
    def output(self):
        return (
            self.selected_session,
            self.selected_signal,
            self.next_step + 1,
            self.recording,
        )

    def panel(self):
        self.set_progress_value(self.next_step)
        return pn.Column(
            pn.Row(self.get_step_static_text(self.next_step)),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            self._select,
        )
