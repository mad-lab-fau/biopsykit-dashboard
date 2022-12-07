import panel as pn
pn.extension(sizing_mode='stretch_width')
pn.extension(notifications=True)
pn.extension('plotly', 'tabulator')
from ECGPipe import *


class MainPage(param.Parameterized):
    welcomeText = ""
    signalSelection = pn.GridBox(ncols=3)
    physBtn = pn.widgets.Button(name="Physiological Data")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    psychBtn = pn.widgets.Button(name="Psychological Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    mainPage = None

    def startPhysPipeline(self, event):
        ecg = ECGPipeline()
        return self.mainPage.append(ecg.pipeline)

    def __init__(self, mainPage, **params):
        f = open('../assets/Markdown/WelcomeText.md', 'r')
        fileString = f.read()
        self.mainPage = mainPage
        self.welcomeText = fileString
        self.physBtn.on_click(self.startPhysPipeline)
        self.signalSelection.append(self.physBtn)
        super().__init__(
            **params)

    def view(self):
        # ecg = ECGPipeline()
        # return ecg.pipeline
        return pn.Column(
            pn.pane.Markdown(self.welcomeText),
            self.signalSelection
        )

