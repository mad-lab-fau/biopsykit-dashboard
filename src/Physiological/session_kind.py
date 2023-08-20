import param
import panel as pn
import pytz

from src.Physiological.PhysiologicalBase import PhysiologicalBase


class SessionKind(PhysiologicalBase):
    synced_radiobox = pn.widgets.RadioBoxGroup(
        name="Synced", options=["Synced", "Not Synced"]
    )

    session = param.Selector(
        default="Single Session", objects=["Multi Session", "Single Session"]
    )

    timezone_select = pn.widgets.Select(
        name="Timezone",
        options=["None Selected"] + list(pytz.all_timezones),
        value="Europe/Berlin",
    )
    text = ""
    ready = param.Boolean(default=True)

    @param.depends("timezone_select.value", watch=True)
    def timezone_selected(self):
        if self.timezone_select.value != "None Selected":
            setattr(self, "ready", True)
        else:
            setattr(self, "ready", False)

    @param.output(
        ("session", param.Dynamic),
        ("synced", param.Boolean),
        ("timezone", param.String),
    )
    def output(self):
        self.synced = self.synced_radiobox.value == "Synced"
        return super().output()

    @param.depends("session", watch=True)
    def session_type_changed(self):
        if self.session == "Multi Session":
            self.synced_radiobox.disabled = False
        else:
            self.synced_radiobox.disabled = True

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/FirstPagePhysiologicalData.md", "r")
            fileString = f.read()
            self.text = fileString
        self.ready = True
        self.synced_radiobox.disabled = True
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.timezone_select,
            self.param.session,
            self.synced_radiobox,
        )
