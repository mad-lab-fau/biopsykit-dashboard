import panel as pn
import biopsykit as bp
import param

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import (
    ASK_TO_CHANGE_FORMAT_TEXT,
    CHANGE_FORMAT_TEXT,
)
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class AskToChangeFormat(QuestionnaireBase):
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    convert_to_long_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Change format"],
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(ASK_TO_CHANGE_FORMAT_TEXT)
        self.skip_btn.link(self, callbacks={"clicks": self.skip_converting_to_long})
        self.convert_to_long_btn.link(
            self, callbacks={"clicks": self.proceed_to_convert_to_long}
        )
        self._view = pn.Column(
            self.header,
            pn.Row(self.convert_to_long_btn, self.skip_btn),
        )

    def skip_converting_to_long(self, target, event):
        self.next_page = "Download Results"
        self.ready = True

    def proceed_to_convert_to_long(self, target, event):
        self.next_page = "Change format"
        self.ready = True

    def panel(self):
        return self._view


class ConvertToLong(QuestionnaireBase):
    converting_panel_column = pn.Column()

    def __init__(self, **params):
        params["HEADER_TEXT"] = CHANGE_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(8)
        self.update_text(CHANGE_FORMAT_TEXT)
        self._view = pn.Column(
            self.header,
            self.converting_panel_column,
        )

    def converting_panel(self) -> pn.pane:
        acc = pn.Accordion()
        for questionnaire in self.dict_scores.keys():
            if not all(
                "_" in x for x in list(self.results.filter(like=questionnaire).columns)
            ):
                continue
            col = pn.Column()
            array_input = pn.widgets.ArrayInput(
                name=f"Index levels for {questionnaire}",
                placeholder='Enter your index levels. E.g. ["subscale","time"]',
            )

            change_btn = pn.widgets.Button(
                name=f"Change format of {questionnaire}",
                button_type="primary",
                disabled=True,
            )
            array_input.link(change_btn, callbacks={"value": self.validate_level_input})
            change_btn.link(
                (questionnaire, array_input), callbacks={"clicks": self.convert_to_long}
            )
            col.append(array_input)
            col.append(change_btn)
            acc.append((questionnaire, col))
        return acc

    @staticmethod
    def validate_level_input(target, event):
        if event.new is not None and len(event.new) != 0:
            target.disabled = False
        else:
            target.enabled = True

    def convert_to_long(self, target, event):
        questionnaire = target[0]
        levels = target[1].value
        if levels is None or len(levels) == 0:
            pn.state.notifications.error(
                "Please type in your desired levels and confirm them with enter"
            )
            return
        try:
            self.data_in_long_format = bp.utils.dataframe_handling.wide_to_long(
                self.results, stubname=questionnaire.upper(), levels=levels
            )
            pn.state.notifications.success(
                f"The format of {questionnaire} is now in long format"
            )
        except Exception as e:
            pn.state.notifications.error(f"The error {e} occurred")

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        if len(self.converting_panel_column.objects) == 0:
            self.converting_panel_column.append(self.converting_panel())
        else:
            self.converting_panel_column.__setitem__(0, self.converting_panel())
        return self._view
