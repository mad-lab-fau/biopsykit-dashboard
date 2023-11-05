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
    welcomeText = ""
    signalSelection = pn.GridBox(ncols=3)
    physBtn = pn.widgets.Button(name="Physiological Data", button_type="light")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    psychBtn = pn.widgets.Button(name="Psychological Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    app = None
    pathToIcons = "./assets/Icons/"
    iconNames = [
        "Physiological.svg",
        "Psychological.svg",
        "Questionnaire.svg",
        "Saliva.svg",
        "Sleep.svg",
    ]
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
        self.app.notifications.info("Starting Pipeline")
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
        homeBtn = pn.widgets.Button(name="Home", button_type="primary")
        homeBtn.on_click(self.get_main_menu)
        physBtn = pn.widgets.Button(name="Physiological Data")
        physBtn.on_click(self.start_pipeline)
        questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
        questionnaireBtn.on_click(self.start_pipeline)
        psychBtn = pn.widgets.Button(name="Psychological Data")
        psychBtn.on_click(self.start_pipeline)
        sleepBtn = pn.widgets.Button(name="Sleep Data")
        sleepBtn.on_click(self.start_pipeline)
        salBtn = pn.widgets.Button(name="Saliva Data")
        salBtn.on_click(self.start_pipeline)
        column = pn.Column(
            homeBtn, physBtn, psychBtn, questionnaireBtn, salBtn, sleepBtn
        )
        return column

    def get_main_menu(self, event):
        self.app.title = "BioPsyKit Dashboard"
        fileString = """
            # Welcome to the BioPsyKit Dashboard

            ## Here you can analyse your Data using the BioPsyKit without any manual programming.

            Please select below one of the Signals you want to analyse. The corresponding guide will help you to get the best out of your data.

            """
        physBtn = pn.widgets.Button(
            name="Physiological Data",
            sizing_mode="stretch_width",
            align="end",
            button_type="primary",
        )
        physBtn.on_click(self.start_pipeline)
        physCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Physiological.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=200,
                styles={"background": "whitesmoke"},
            ),
            pn.Spacer(height=45),
            physBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
        sleepBtn = pn.widgets.Button(
            name="Sleep Data",
            sizing_mode="stretch_width",
            align="end",
            button_type="primary",
        )
        sleepBtn.on_click(self.start_pipeline)
        sleepCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Sleep.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=160,
                fixed_aspect=False,
            ),
            pn.Spacer(height=45),
            sleepBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
        questionnaireBtn = pn.widgets.Button(
            name="Questionnaire Data",
            sizing_mode="stretch_width",
            button_type="primary",
        )
        questionnaireBtn.on_click(self.start_pipeline)
        questionnaireCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Questionnaire.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=150,
                styles={"background": "whitesmoke"},
            ),
            pn.Spacer(height=45),
            questionnaireBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
        psychBtn = pn.widgets.Button(
            name="Psychological Data",
            sizing_mode="stretch_width",
            button_type="primary",
        )
        psychBtn.on_click(self.start_pipeline)
        psychCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Psychological.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=150,
                styles={"background": "whitesmoke"},
            ),
            pn.Spacer(height=45),
            psychBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
        salBtn = pn.widgets.Button(
            name="Saliva Data",
            sizing_mode="stretch_width",
            button_type="primary",
        )
        salBtn.on_click(self.start_pipeline)
        salCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Saliva.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=150,
                styles={"background": "whitesmoke"},
            ),
            pn.Spacer(height=45),
            salBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
        signalSelection = pn.GridBox(
            *[physCard, psychCard, questionnaireCard, salCard, sleepCard],
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
        self.signalSelection.append(self.physBtn)
        super().__init__(**params)
        self._view = pn.Column(pn.pane.Markdown(self.welcomeText), self.signalSelection)

    def view(self):
        return self._view
