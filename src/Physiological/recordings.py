import panel as pn
import param

from src.Physiological.PhysiologicalBase import PhysiologicalBase


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
        self._select.link(self, callbacks={"value": self.chg})
        self.set_progress_value(self.next_step)
        self._view = pn.Column(
            pn.Row(self.get_step_static_text(self.next_step)),
            pn.Row(self.get_progress(self.step)),
            pn.pane.Markdown(self.text),
            self._select,
        )

    def chg(self, target, event):
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        self.set_progress_value(self.next_step)
        return self._view
