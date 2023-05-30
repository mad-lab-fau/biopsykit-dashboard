import param
import panel as pn

from src.utils import load_subject_condition_list


class AskToLoadConditionList(param.Parameterized):
    no_condition_list_btn = pn.widgets.Button(name="No")
    add_condtion_list_btn = pn.widgets.Button(name="Yes")
    ready = param.Boolean(default=False)
    format = param.String(default=None)
    next_page = param.Selector(
        default="Add Condition List",
        objects=[
            "Add Condition List",
            "Load Saliva Data Plate Format",
            "Load Saliva Data Wide Format",
        ],
    )

    def no_condition_list(self, target, event):
        if "Wide" in self.format:
            self.next_page = "Load Saliva Data Wide Format"
        else:
            self.next_page = "Load Saliva Data Plate Format"
        self.ready = True

    def add_condition_list(self, target, event):
        self.next_page = "Add Condition List"
        self.ready = True

    @param.output(
        ("format", param.String),
    )
    def output(self):
        return (self.format,)

    def panel(self):
        self.no_condition_list_btn.link(
            self, callbacks={"clicks": self.no_condition_list}
        )
        self.add_condtion_list_btn.link(
            self, callbacks={"clicks": self.add_condition_list}
        )
        return pn.Column(
            pn.pane.Markdown("# Do you want to add a condition list?"),
            pn.Row(self.no_condition_list_btn, self.add_condtion_list_btn),
        )


class AddConditionList(param.Parameterized):
    condition_list = param.Dynamic(default=None)
    ready = param.Boolean(default=False)
    format = param.String(default=None)
    upload_condition_list_btn = pn.widgets.FileInput(
        name="Upload condition list", accept=".csv,.xls,.xlsx", multiple=False
    )
    next = param.Selector(
        default="Load Saliva Data Plate Format",
        objects=[
            "Load Saliva Data Plate Format",
            "Load Saliva Data Wide Format",
        ],
    )

    def parse_file_input(self, target, event):
        try:
            self.condition_list = load_subject_condition_list(
                self.upload_condition_list_btn.value,
                self.upload_condition_list_btn.filename,
            )
            pn.state.notifications.success("Condition List successfully loaded")
            self.ready = True
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    @param.output(
        ("condition_list", param.Dynamic),
        ("format", param.String),
    )
    def output(self):
        return (
            self.condition_list,
            self.format,
        )

    def panel(self):
        if "Wide" in self.format:
            self.next = "Load Saliva Data Wide Format"
        else:
            self.next = "Load Saliva Data Plate Format"
        self.upload_condition_list_btn.link(
            self, callbacks={"value": self.parse_file_input}
        )
        return pn.Column(
            pn.pane.Markdown("# Add condition list"),
            self.upload_condition_list_btn,
        )
