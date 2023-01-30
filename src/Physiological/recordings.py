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

    def chg(self, _, event):
        if event.new == "Single Recording":
            self.next = "Upload Files"
        else:
            self.next = "Multiple Files"

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/number_of_recordings.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.step = 2
        self.set_progress_value()
        self.recording.link(
            "subject",
            callbacks={"value": self.chg},
        )
        return pn.Column(
            pn.Row(self.get_step_static_text()),
            pn.Row(self.progress),
            pn.pane.Markdown(self.text),
            self.recording,
        )
