import panel as pn
import param

from src.MainPage.MAIN_CONSTANTS import WELCOME_TEXT
from src.Physiological.physiological_pipeline import *

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
    mainPage = None

    def start_physiological_pipeline(self, event):
        ecg = PhysiologicalPipeline()
        return self.mainPage.append(pn.Column(ecg.pipeline))

    def __init__(self, main_page, **params):
        self.mainPage = main_page
        self.welcomeText = WELCOME_TEXT
        self.physBtn.on_click(self.start_physiological_pipeline)
        self.signalSelection.append(self.physBtn)
        super().__init__(**params)

    def view(self):
        return pn.Column(pn.pane.Markdown(self.welcomeText), self.signalSelection)