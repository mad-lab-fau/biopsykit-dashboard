import panel as pn
import param
from src.Physiological.recordings import Recordings


class Compress(Recordings):
    def __init__(self):
        super().__init__()
        self.step = 4
        self.text = (
            "# Compress your Files\n"
            "Because you selected, that you want to analyse more than one File,"
            "you have to compress the content of your Folder into one .zip File.\n"
            "Please do that before proceeding to the next step.\n"
        )
        self.set_progress_value(self.step)
        self._view = pn.Column(
            pn.Row(self.get_step_static_text(self.step)),
            pn.Row(self.get_progress(self.step)),
            pn.pane.Markdown(self.text),
        )

    def panel(self):
        return self._view
