import panel as pn
import param

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class Recordings(PhysiologicalBase):

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
        text = (
            "# Number of Recordings \n"
            "After you defined the kind of Sessions, in this step you will set if your data"
            "consists of a single Recording or multiple recordings.\n\n"
            "A single Recording means, that you only have one file per subject and multiple Recording"
            "is defined as two or more files per subject. \n"
        )
        self.update_text(text)
        self.ready = True
        self._select = pn.widgets.Select.from_param(self.param.recording)
        self._select.link(self, callbacks={"value": self.chg})
        self.set_progress_value(self.step)
        self._view = pn.Column(
            self.header,
            self._select,
        )

    def chg(self, target, event):
        if self.recording == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):

        return self._view
