import panel as pn
import param
import biopsykit as bp
from biopsykit.utils.exceptions import ValidationError

from src.Questionnaire.QUESTIONNAIRE_CONSTANTS import (
    ASK_TO_CONVERT_SCALES_TEXT,
    CONVERT_SCALES_TEXT,
)
from src.Questionnaire.questionnaire_base import QuestionnaireBase


class AskToConvertScales(QuestionnaireBase):
    next_page = param.Selector(
        default="Convert Scales",
        objects=["Convert Scales", "Ask To crop scales"],
    )
    convert_scales_btn = pn.widgets.Button(name="Yes")
    skip_converting_btn = pn.widgets.Button(name="No", button_type="primary")
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_TO_CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(ASK_TO_CONVERT_SCALES_TEXT)
        self.convert_scales_btn.link(self, callbacks={"clicks": self.convert_scales})
        self.skip_converting_btn.link(self, callbacks={"clicks": self.skip_converting})
        self._view = pn.Column(
            self.header,
            pn.Row(
                self.convert_scales_btn,
                self.skip_converting_btn,
            ),
        )

    def convert_scales(self, _, event):
        self.next_page = "Convert Scales"
        self.ready = True

    def skip_converting(self, _, event):
        self.next_page = "Ask To crop scales"
        self.ready = True

    def panel(self):
        return self._view


class ConvertScales(QuestionnaireBase):
    convert_column = pn.Column(sizing_mode="stretch_width")
    change_questionnaires_btn = pn.widgets.Button(name="Change Questionnaire scales")
    change_columns_btn = pn.widgets.Button(name="Change Columns", button_type="primary")
    change_columns_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )
    questionnaire_col = pn.Column(
        sizing_mode="stretch_width", visible=False, objects=[pn.Column(name=None)]
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = CONVERT_SCALES_TEXT
        super().__init__(**params)
        self.update_step(5)
        self.update_text(CONVERT_SCALES_TEXT)
        self.change_questionnaires_btn.link(
            self.questionnaire_col, callbacks={"clicks": self.show_questionnaire_col}
        )
        self.change_columns_btn.link(
            self.change_columns_col, callbacks={"clicks": self.show_name_col}
        )

    @staticmethod
    def activate_btn(target, event):
        if event.new is not None:
            target.disabled = False
        else:
            target.disabled = True

    @staticmethod
    def activate_col_btn(target, event):
        if type(event.new) is list:
            if len(event.new) == 0 or target[0].value is None:
                target[1].disabled = True
                return
        else:
            if event.new is None or len(target[0].value) == 0:
                target[1].disabled = True
                return
        target[1].disabled = False

    def apply_questionnaire_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        if self.data is None or self.data.empty or self.dict_scores is None:
            return
        key = target[0].value
        offset = target[1].value
        if key is None or not isinstance(key, str):
            pn.state.notifications.warning("No Questionnaire selected")
            return
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if key not in self.dict_scores.keys():
            pn.state.notifications.warning("No Questionnaire selected")
            return
        try:
            cols = self.dict_scores[key].to_list()
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of the questionnaire: {key} by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")

    def apply_column_scale(self, target, _):
        if type(target) is not tuple or len(target) != 2:
            return
        cols = target[0].value
        if cols is None or len(cols) == 0:
            pn.state.notifications.warning("No Columns selected")
            return
        offset = target[1].value
        if offset is None or not isinstance(offset, int):
            pn.state.notifications.warning("No offset selected")
            return
        if any([col not in self.data.columns.to_list() for col in cols]):
            pn.state.notifications.warning("Not all columns are in the data")
            return
        try:
            self.data_scaled = bp.questionnaires.utils.convert_scale(
                self.data, cols=cols, offset=offset
            )
            pn.state.notifications.success(
                f"Changed the scaling of {len(cols)} Columns by offset: {offset}"
            )
        except ValidationError as e:
            pn.state.notifications.error(f"Validation Error: {e}")
        except KeyError as ke:
            pn.state.notifications.error(f"Key Error: {ke}")

    def show_questionnaire_col(self, _, event):
        self.questionnaire_col.visible = True
        self.change_columns_col.visible = False
        if len(self.questionnaire_col.objects) == 0:
            self.questionnaire_col.append(self.get_questionnaire_col())
        elif len(self.questionnaire_col.objects) > 1:
            while len(self.questionnaire_col.objects) > 1:
                self.questionnaire_col.pop(0)
        elif (
            len(self.questionnaire_col.objects) == 1
            and self.questionnaire_col.objects[0].name is None
        ):
            self.questionnaire_col.__setitem__(0, self.get_questionnaire_col())

    def show_name_col(self, target, _):
        self.questionnaire_col.visible = False
        self.change_columns_col.visible = True
        if len(self.change_columns_col.objects) == 0:
            self.change_columns_col.append(self.get_column_col())
        elif len(self.change_columns_col.objects) > 1:
            while len(self.change_columns_col.objects) > 1:
                self.change_columns_col.pop(0)
        elif (
            len(self.change_columns_col.objects) == 1
            and self.change_columns_col.objects[0].name is None
        ):
            self.change_columns_col.__setitem__(0, self.get_column_col())

    def get_questionnaire_col(self) -> pn.Column:
        quest_col = pn.Column()
        select = pn.widgets.Select(
            name="Select Questionnaire", options=list(self.dict_scores.keys())
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder="Enter an offset for the selected columns",
            value=None,
        )
        row = pn.Row()
        row.append(select)
        row.append(input_offset)
        quest_col.append(row)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link(btn, callbacks={"value": self.activate_btn})
        btn.link(
            (select, input_offset),
            callbacks={"clicks": self.apply_questionnaire_scale},
        )
        quest_col.append(btn)
        return quest_col

    def get_column_col(self) -> pn.Column:
        col = pn.Column()
        crSel = pn.widgets.CrossSelector(
            name="Columns to invert the data",
            options=self.data.columns.to_list(),
            height=min(400, 100 + len(self.data.columns.tolist()) * 5),
        )
        input_offset = pn.widgets.IntInput(
            name="Offset",
            placeholder=f"Enter an offset for the selected columns",
            value=None,
        )
        col.append(crSel)
        col.append(input_offset)
        btn = pn.widgets.Button(
            name="Apply Changes", button_type="primary", disabled=True
        )
        input_offset.link((crSel, btn), callbacks={"value": self.activate_col_btn})
        crSel.link((input_offset, btn), callbacks={"value": self.activate_col_btn})
        btn.link((crSel, input_offset), callbacks={"clicks": self.apply_column_scale})
        col.append(btn)
        return col

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        return pn.Column(
            self.header,
            pn.Row(
                self.change_questionnaires_btn,
                self.change_columns_btn,
            ),
            self.convert_column,
            self.questionnaire_col,
            self.change_columns_col,
        )
