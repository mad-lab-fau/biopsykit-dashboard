import panel as pn
import param

from src.MainPage.MAIN_CONSTANTS import WELCOME_TEXT
from src.Physiological.physiological_pipeline import *
from src.Psychological.psychological_pipeline import PsychologicalPipeline
from src.Questionnaire.questionnaire_pipeline import QuestionnairePipeline
from src.Saliva.saliva_pipeline import SalivaPipeline
from src.Sleep.sleep_pipeline import SleepPipeline

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")


class MainPage(param.Parameterized):
    app = None
    name_pipeline_dict = {
        "Physiological Data": PhysiologicalPipeline(),
        "Psychological Data": PsychologicalPipeline(),
        "Questionnaire Data": QuestionnairePipeline(),
        "Saliva Data": SalivaPipeline(),
        "Sleep Data": SleepPipeline(),
    }

    def start_pipeline(self, event):
        pipeline_name = event.obj.name
        if pipeline_name is None or pipeline_name not in self.name_pipeline_dict.keys():
            pn.state.notifications.error("No Pipeline found for this Button")
            return
        pipeline = self.name_pipeline_dict[pipeline_name]
        pane = pn.Column(
            pn.Row(
                pn.layout.HSpacer(),
                pipeline.pipeline.prev_button,
                pipeline.pipeline.next_button,
            ),
            pipeline.pipeline.stage,
            min_height=2000,
        )
        self.app.main[0].objects = [pane]

    def get_sidebar(self):
        column = pn.Column()
        homeBtn = pn.widgets.Button(name="Home", button_type="primary")
        homeBtn.on_click(self.get_main_menu)
        column.append(homeBtn)
        for pipeline in self.name_pipeline_dict.keys():
            btn = pn.widgets.Button(
                name=pipeline,
                button_type="light",
                icon=self.name_pipeline_dict[pipeline].icon_name,
            )
            btn.on_click(self.start_pipeline)
            column.append(btn)
        return column

    def get_main_menu(self, event):
        self.app.title = "BioPsyKit Dashboard"
        fileString = """
            # Welcome to the BioPsyKit Dashboard

            ## Here you can analyse your Data using the BioPsyKit without any manual programming.

            Please select below one of the Signals you want to analyse. The corresponding guide will help you to get the best out of your data.

            """
        card_list = []
        for pipeline_name in self.name_pipeline_dict.keys():
            btn = pn.widgets.Button(
                name=pipeline_name,
                sizing_mode="stretch_width",
                align="end",
                button_type="primary",
            )
            btn.on_click(self.start_pipeline)
            card = pn.GridBox(
                pn.pane.SVG(
                    self.name_pipeline_dict[pipeline_name].icon_svg,
                    align=("center"),
                    sizing_mode="stretch_both",
                    max_height=150,
                    max_width=200,
                    styles={"background": "whitesmoke"},
                ),
                pn.Spacer(height=45),
                btn,
                ncols=1,
                styles={"background": "whitesmoke", "align": "center"},
                width=250,
                height=250,
            )
            card_list.append(card)
        signalSelection = pn.GridBox(
            *card_list,
            ncols=3,
            nrows=2,
            max_width=1000,
            height=600,
        )
        pane = pn.Column(pn.pane.Markdown(fileString), signalSelection)
        if len(self.app.main) > 0:
            self.app.main[0].objects = [pane]
        else:
            self.app.main.append(pane)

    def __init__(self, app, **params):
        self.app = app
        self.welcomeText = WELCOME_TEXT
        super().__init__(**params)
        self._view = pn.Column(pn.pane.Markdown(self.welcomeText))

    def view(self):
        return self._view
