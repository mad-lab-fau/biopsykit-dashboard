import panel as pn
import biopsykit as bp
import param


class AskToChangeFormat(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    results = param.Dynamic()
    ready = param.Boolean(default=False)
    skip_btn = pn.widgets.Button(name="No", button_type="primary")
    convert_to_long_btn = pn.widgets.Button(name="Yes")
    next_page = param.Selector(
        default="Download Results",
        objects=["Download Results", "Change format"],
    )

    def skip_converting_to_long(self, target, event):
        self.next_page = "Download Results"
        self.ready = True

    def proceed_to_convert_to_long(self, target, event):
        self.next_page = "Change format"
        self.ready = True

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
        ("results", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.dict_scores,
            self.data_scores,
            self.data_scaled,
            self.results,
        )

    def panel(self):
        self.skip_btn.link(None, callbacks={"clicks": self.skip_converting_to_long})
        self.convert_to_long_btn.link(
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
        row.append(self.convert_to_long_btn)
        row.append(self.skip_btn)
        col.append(row)
        return col


class ConvertToLong(param.Parameterized):
    data = param.Dynamic()
    dict_scores = param.Dict()
    data_scores = param.Dynamic()
    data_scaled = param.Dynamic()
    results = param.Dynamic()

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

    def validate_level_input(self, target, event):
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
            t = bp.utils.dataframe_handling.wide_to_long(
                self.results, stubname=questionnaire.upper(), levels=levels
            )
            pn.state.notifications.success(
                f"The format of {questionnaire} is now in long format"
            )
        except Exception as e:
            pn.state.notifications.error(f"The error {e} occured")

    @param.output(
        ("data", param.Dynamic),
        ("dict_scores", param.Dict),
        ("data_scores", param.Dynamic),
        ("data_scaled", param.Dynamic),
        ("results", param.Dynamic),
    )
    def output(self):
        return (
            self.data,
            self.dict_scores,
            self.data_scores,
            self.data_scaled,
            self.results,
        )

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
