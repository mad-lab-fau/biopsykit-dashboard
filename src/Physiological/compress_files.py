import panel as pn
import param
from src.Physiological.recordings import Recordings


class Compress(Recordings):
    selected_session = param.String()
    selected_signal = param.String()
    recordings = param.String()

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

    @param.output(
        ("selected_session", param.Dynamic),
        ("selected_signal", param.String),
        ("recordings", param.String),
    )
    def output(self):
        return (
            self.selected_session,
            self.selected_signal,
            self.recording,
        )

    def panel(self):
        return self._view
