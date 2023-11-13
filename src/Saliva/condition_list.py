import param
import panel as pn

from src.Saliva.SALIVA_CONSTANTS import (
    ASK_TO_LOAD_CONDITION_LIST_TEXT,
    ADD_CONDITION_LIST_TEXT,
)
from src.Saliva.SalivaBase import SalivaBase
from src.utils import load_subject_condition_list


class AskToLoadConditionList(SalivaBase):
    no_condition_list_btn = pn.widgets.Button(
        name="No", button_type="primary", sizing_mode="stretch_width"
    )
    add_condition_list_btn = pn.widgets.Button(
        name="Yes", sizing_mode="stretch_width", button_type="light"
    )
    ready = param.Boolean(default=False)
    next_page = param.Selector(
        default="Add Condition List",
        objects=[
            "Add Condition List",
            "Load Saliva Data",
        ],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_LOAD_CONDITION_LIST_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(ASK_TO_LOAD_CONDITION_LIST_TEXT)
        self.no_condition_list_btn.link(
            self, callbacks={"clicks": self.no_condition_list}
        )
        self.add_condition_list_btn.link(
            self, callbacks={"clicks": self.add_condition_list}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.add_condition_list_btn, self.no_condition_list_btn),
        )

    def no_condition_list(self, _, event):
        self.next_page = "Load Saliva Data"
        self.ready = True

    def add_condition_list(self, _, event):
        self.next_page = "Add Condition List"
        self.ready = True

    def panel(self):
        return self._view


class AddConditionList(SalivaBase):
    ready = param.Boolean(default=False)
    upload_condition_list_btn = pn.widgets.FileInput(
        name="Upload condition list",
        accept=".csv,.xls,.xlsx",
        multiple=False,
        sizing_mode="stretch_width",
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ADD_CONDITION_LIST_TEXT
        super().__init__(**params)
        self.update_step(2)
        self.update_text(ADD_CONDITION_LIST_TEXT)
        self.upload_condition_list_btn.link(
            self, callbacks={"filename": self.filename_changed}
        )
        self._view = pn.Column(
            self.header,
            self.upload_condition_list_btn,
        )

    def filename_changed(self, _, event):
        filename = event.new
        if (
            filename is None
            or filename == ""
            or "." not in filename
            or self.upload_condition_list_btn.value is None
        ):
            self.ready = False
            return
        else:
            self.parse_file_input(filename)

    def parse_file_input(self, filename: str):
        try:
            self.condition_list = load_subject_condition_list(
                self.upload_condition_list_btn.value,
                filename,
            )
            pn.state.notifications.success("Condition List successfully loaded")
            self.ready = True
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False

    def panel(self):
        return self._view
