import panel as pn
import param
import biopsykit as bp


class AskToConvertScales(param.Parameterized):
    text = ""
    data = param.Dynamic()
    dict_scores = param.Dict()
    col = pn.Column(sizing_mode="stretch_width")
    next_page = param.Selector(
        default="Convert Scales",
        objects=["Convert Scales", "Show Results"],
    )
    convert_scales_btn = pn.widgets.Button(name="Yes")
    skip_converting_btn = pn.widgets.Button(name="No", button_type="primary")
    ready = param.Boolean(default=False)

    def convert_scales(self, _):
        self.next_page = "Convert Scales"
        self.ready = True

    def skip_converting(self, _):
        self.next_page = "Show Results"
        self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
    )
    def output(self):
        if self.next_page == "Show Results":
            return (
                self.data,
                self.dict_scores,
                bp.questionnaires.utils.compute_scores(
                    data=self.data, quest_dict=self.dict_scores
                ),
            )
        return (self.data, self.dict_scores, None)

    def panel(self):
        if self.text == "":
            f = open("../assets/Markdown/AskToConvertScales.md", "r")
            fileString = f.read()
            self.text = fileString
        self.convert_scales_btn.on_click(self.convert_scales)
        self.skip_converting_btn.on_click(self.skip_converting)
        self.col = pn.Column(sizing_mode="stretch_width")
        self.col.append(pn.pane.Markdown(self.text))
        row = pn.Row()
        row.append(self.convert_scales_btn)
        row.append(self.skip_converting_btn)
        self.col.append(row)
        return self.col


class ConvertScales(param.Parameterized):
    text = "# Convert Scales"
    data = param.Dynamic()
    data_scaled = None
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    col = pn.Column(sizing_mode="stretch_width")
    change_questionnaires_btn = pn.widgets.Button(name="Change Questionnaire scales")
    change_columns_btn = pn.widgets.Button(name="Change Columns", button_type="primary")
    change_columns_col = pn.Column(sizing_mode="stretch_width", visible=False)
    questionnaire_col = pn.Column(sizing_mode="stretch_width", visible=False)

    @staticmethod
    def activate_btn(target, event):
        if event.new is not None:
            target.disabled = False
        else:
            target.disabled = True

    def activate_col_btn(self, target, event):
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
        key = target[0].value
        offset = target[1].value
        cols = self.dict_scores[key].to_list()
        self.data_scaled = bp.questionnaires.utils.convert_scale(
            self.data, cols=cols, offset=offset
        )
        pn.state.notifications.success(
            f"Changed the scaling of the questionnaire: {key} by offset: {offset}"
        )

    def apply_column_scale(self, target, _):
        cols = target[0].value
        offset = target[1].value
        self.data_scaled = bp.questionnaires.utils.convert_scale(
            self.data, cols=cols, offset=offset
        )
        pn.state.notifications.success(
            f"Changed the scaling of {len(cols)} Columns by offset: {offset}"
        )

    def show_questionnaire_col(self, target, event):
        if len(self.col.objects) == 3 and self.col.objects[2] == self.questionnaire_col:
            return
        self.questionnaire_col = self.get_questionnaire_col()
        self.questionnaire_col.visible = True
        if len(self.col.objects) == 3:
            self.col.pop(2)
        self.col.append(self.questionnaire_col)

    def show_name_col(self, target, event):
        if (
            len(self.col.objects) == 3
            and self.col.objects[2] == self.change_columns_col
        ):
            return
        self.change_columns_col = self.get_column_col()
        self.change_columns_col.visible = True
        if len(self.col.objects) == 3:
            self.col.pop(2)
        self.col.append(self.change_columns_col)

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
            (select, input_offset), callbacks={"clicks": self.apply_questionnaire_scale}
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
        if len(self.col.objects) > 0:
            return self.col
        self.col = pn.Column(sizing_mode="stretch_width")
        self.col.append(pn.pane.Markdown(self.text))
        row = pn.Row()
        row.append(self.change_questionnaires_btn)
        row.append(self.change_columns_btn)
        self.col.append(row)
        self.change_questionnaires_btn.link(
            self.questionnaire_col, callbacks={"clicks": self.show_questionnaire_col}
        )
        self.change_columns_btn.link(
            self.change_columns_col, callbacks={"clicks": self.show_name_col}
        )
        return self.col
