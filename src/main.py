import panel as pn

from src.Questionnaire.questionnaire_pipeline import QuestionnairePipeline
from src.Saliva.saliva_pipeline import SalivaPipeline

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
from main_page import *


app = pn.template.FastListTemplate(
    title="BioPysKit Dashboard",
    header_background="#186FEF",
    logo="../assets/Icons/biopsykit_Icon.png",
    favicon="../assets/Favicon/bio.ico",
)
app.sidebar.constant = False
app.main.constant = False
app.theme_toggle = False
current_page = pn.Column()
current_page = MainPage(app.main)


def startPhysPipeline(event):
    ecg = PhysiologicalPipeline()
    pane = pn.Column(
        pn.Row(
            # ecg.pipeline.title,
            pn.layout.HSpacer(),
            ecg.pipeline.prev_button,
            ecg.pipeline.next_button,
        ),
        ecg.pipeline.stage,
    )
    app.main[0].objects = [pane]


def startQuestionnairePipeline(event):
    questionnaire = QuestionnairePipeline()
    pane = pn.Column(
        pn.Row(
            pn.layout.HSpacer(),
            questionnaire.pipeline.prev_button,
            questionnaire.pipeline.next_button,
        ),
        questionnaire.pipeline.stage,
    )
    app.main[0].objects = [pane]


def startSalivaPipeline(event):
    questionnaire = SalivaPipeline()
    pane = pn.Column(
        pn.Row(
            pn.layout.HSpacer(),
            questionnaire.pipeline.prev_button,
            questionnaire.pipeline.next_button,
        ),
        questionnaire.pipeline.stage,
        min_height=2000,
    )
    app.main[0].objects = [pane]


def get_sidebar():
    homeBtn = pn.widgets.Button(name="Home", button_type="primary")
    homeBtn.on_click(get_mainMenu)
    physBtn = pn.widgets.Button(name="Physiological Data")
    physBtn.on_click(startPhysPipeline)
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    questionnaireBtn.on_click(startQuestionnairePipeline)
    psychBtn = pn.widgets.Button(name="Psychological Data")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    salBtn.on_click(startSalivaPipeline)
    column = pn.Column(homeBtn, physBtn, psychBtn, questionnaireBtn, salBtn, sleepBtn)
    return column


def get_mainMenu(event):
    f = open("../assets/Markdown/WelcomeText.md", "r")
    fileString = f.read()
    physBtn = pn.widgets.Button(
        name="Physiological Data", sizing_mode="stretch_width", align="end"
    )
    physBtn.on_click(startPhysPipeline)
    sleepBtn = pn.widgets.Button(
        name="Sleep Data", sizing_mode="stretch_width", align="end"
    )
    questionnaireBtn = pn.widgets.Button(
        name="Questionnaire Data", sizing_mode="stretch_width"
    )
    questionnaireBtn.on_click(startQuestionnairePipeline)
    psychBtn = pn.widgets.Button(name="Psychological Data", sizing_mode="stretch_width")
    salBtn = pn.widgets.Button(name="Saliva Data", sizing_mode="stretch_width")
    salBtn.on_click(startSalivaPipeline)
    pathToIcons = "../assets/Icons/"
    iconNames = [
        "Physiological.svg",
        "Psychological.svg",
        "Questionnaire.svg",
        "Saliva.svg",
        "Sleep.svg",
    ]
    physCard = pn.Card(
        pn.pane.SVG(
            pathToIcons + iconNames[0],
            align="center",
            sizing_mode="stretch_both",
            max_height=150,
            max_width=200,
            background="whitesmoke",
        ),
        pn.Spacer(height=45),
        physBtn,
        collapsible=False,
        height=250,
        background="whitesmoke",
        hide_header=True,
    )
    psychCard = pn.Card(
        pn.pane.SVG(
            pathToIcons + iconNames[1],
            align="center",
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            background="whitesmoke",
        ),
        pn.Spacer(height=45),
        psychBtn,
        collapsible=False,
        height=250,
        background="whitesmoke",
        hide_header=True,
    )
    questionnaireCard = pn.Card(
        pn.pane.SVG(
            pathToIcons + iconNames[2],
            align="center",
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            background="whitesmoke",
        ),
        pn.Spacer(height=45),
        questionnaireBtn,
        collapsible=False,
        height=250,
        background="whitesmoke",
        hide_header=True,
    )
    salCard = pn.Card(
        pn.pane.SVG(
            pathToIcons + iconNames[3],
            align="center",
            sizing_mode="stretch_both",
            max_height=150,
            max_width=150,
            background="whitesmoke",
        ),
        pn.Spacer(height=45),
        salBtn,
        collapsible=False,
        height=250,
        background="whitesmoke",
        hide_header=True,
    )
    sleepCard = pn.Card(
        pn.pane.SVG(
            pathToIcons + iconNames[4],
            align="center",
            sizing_mode="stretch_both",
            max_height=150,
            max_width=160,
            background="whitesmoke",
        ),
        pn.Spacer(height=45),
        sleepBtn,
        collapsible=False,
        height=250,
        background="whitesmoke",
        hide_header=True,
    )
    signalSelection = pn.GridBox(
        *[physCard, psychCard, questionnaireCard, salCard, sleepCard], ncols=3
    )
    pane = pn.Column(pn.pane.Markdown(fileString), signalSelection)
    if len(app.main) > 0:
        app.main[0].objects = [pane]
    else:
        app.main.append(pane)


# def main():


if __name__ == "__main__":
    app.sidebar.append(get_sidebar())
    get_mainMenu(None)
    app.servable().show(
        port=5023,
        verbose=True,
        autoreload=True,
    )
# ssl_certfile = "localhost.crt",
# ssl_keyfile = "localhost.key",
