import panel as pn
import biopsykit as bp
import param


class AskToChangeFormat(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    convert_to_long_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Show Results",
        objects=["Show Results", "Change Format"],
    )

    def skip_converting_to_long(self, target, event):
        self.next_page = "Show Results"
        self.ready = True

    def proceed_to_convert_to_long(self, target, event):
        self.next_page = "Change Format"
        self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
    )
    def output(self):
        return (self.data, self.dict_scores, self.data_scores, self.data_scaled)

    def panel(self):
        self.skip_btn.link(None, callbacks={"clicks": self.skip_converting_to_long})
        self.convert_to_long_btn(
            None, callbacks={"clicks": self.proceed_to_convert_to_long}
        )
        text = (
            "# Do you want to change the format of your Dataframes? \n "
            'If wou want to divide the Data of your questionnaires into different subscales please click on "Yes" '
            "otherwise you may skip that step"
        )
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        row = pn.Row()
        row.append(self.skip_btn)
        row.append(self.convert_to_long_btn)
        col.append(row)
        return col


class ConvertToLong(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()

    def converting_panel(self) -> pn.pane:
        acc = pn.Accordion()
        for questionnaire in self.data_scaled.keys():
            if not all(x.contains("_") for x in self.data_scaled[questionnaire]):
                continue
            col = pn.Column()
            array_input = pn.widgets.ArrayInput(
                name="Index levels for your questionnaire"
            )
            change_btn = pn.widgets.Button(name=f"Change format of {questionnaire}")
            col.append(array_input)
            col.append(change_btn)
            acc.append((questionnaire, col))
        return acc

    def panel(self):
        if self.data_scaled is None:
            self.data_scaled = self.data
        text = (
            "# Convert from wide to long format \n "
            "In this step you can change the format of the datframe(s) of your questionnaire(s).\n"
            "Below you can select from the questionnaire(s) of the provided data in order to change the format."
            ' However only those questionnaire(s) which include column(s) that contain the symbol "_" are shown.'
        )
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        col.append(self.converting_panel())
        return col
