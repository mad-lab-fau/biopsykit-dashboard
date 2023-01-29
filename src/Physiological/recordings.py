import panel as pn
import param

from src.Physiological.sessions import Session


class Recordings(Session):
    recording = pn.widgets.Select(
        value="Single Recording", options=["Multiple Recording", "Single Recording"]
    )
    next = param.Selector(
        default="Upload Files", objects=["Upload Files", "Multiple Files"]
    )

    @pn.depends("recording.value", watch=True)
    def change_path(self):
        if self.recording.value == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/number_of_recordings.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.step.value = "Step 2 of " + str(self.max_steps)
        return pn.Column(
            pn.Row(self.step),
            pn.pane.Markdown(self.text),
            self.recording,
        )
