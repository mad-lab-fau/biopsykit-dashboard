import param
import panel as pn

from src.utils import load_subject_condition_list


class AskToLoadConditionList(param.Parameterized):
    no_condition_list_btn = pn.widgets.Button(name="No")
    add_condtion_list_btn = pn.widgets.Button(name="Yes")
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Add condition list", objects=["Add condition list", "Load Saliva Data"]
    )

    def no_condition_list(self, target, event):
        self.ready = True
        self.next_page = "Load Saliva Data"

    def add_condition_list(self, target, event):
        self.ready = True
        self.next_page = "Add condition list"

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
    upload_condition_list_btn = pn.widgets.FileInput(
        name="Upload condition list", accept=".csv,.xls,.xlsx", multiple=False
    )

    def parse_file_input(self, target, event):
        try:
            self.condition_list = load_subject_condition_list(
                self.upload_condition_list_btn.value,
                self.upload_condition_list_btn.filename,
            )
            pn.state.notifications.success("Condition List successfully loaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    @param.output(
        ("condition_list", param.Dynamic),
    )
    def output(self):
        return (self.condition_list,)

    def panel(self):
        self.upload_condition_list_btn.link(
            self, callbacks={"value": self.parse_file_input}
        )
        return pn.Column(
            pn.pane.Markdown("# Add condition list"),
            self.upload_condition_list_btn,
        )
