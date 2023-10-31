import os

os.environ["OUTDATED_IGNORE"] = "1"
import panel as pn

from src.Physiological.physiological_pipeline import PhysiologicalPipeline

pn.extension(sizing_mode="stretch_width")
pn.extension(
    "plotly",
    sizing_mode="stretch_width",
)
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
from src.MainPage.main_page import MainPage

app = pn.template.BootstrapTemplate(
    title="BioPysKit Dashboard",
    header_background="#186FEF",
    logo="./assets/Icons/biopsykit_Icon.png",
)

app.config.console_output = "disable"
app.config.log_level = "CRITICAL"
app.sidebar.constant = False
app.main.constant = False
app.theme_toggle = False
current_page = MainPage(app.main)


def startPipeline(event):
    btn_name = event.obj.name
    if "Physiological" in btn_name:
        pipeline = PhysiologicalPipeline()
    # elif "Sleep" in btn_name:
    #     pipeline = SleepPipeline()
    # elif "Questionnaire" in btn_name:
    #     pipeline = QuestionnairePipeline()
    # elif "Saliva" in btn_name:
    #     pipeline = SalivaPipeline()
    # elif "Psychological" in btn_name:
    #     pipeline = PsychologicalPipeline()
    else:
        pn.state.notifications.error("No Pipeline found for this Button")
        return
    pane = pn.Column(
        pn.Row(
            pn.layout.HSpacer(),
            pipeline.pipeline.prev_button,
            pipeline.pipeline.next_button,
        ),
        pipeline.pipeline.stage,
        min_height=2000,
    )
    app.main[0].objects = [pane]


def get_sidebar():
    homeBtn = pn.widgets.Button(name="Home", button_type="primary")
    homeBtn.on_click(get_mainMenu)
    physBtn = pn.widgets.Button(name="Physiological Data")
    physBtn.on_click(startPipeline)
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    questionnaireBtn.on_click(startPipeline)
    psychBtn = pn.widgets.Button(name="Psychological Data")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    salBtn.on_click(startPipeline)
    column = pn.Column(homeBtn, physBtn, psychBtn, questionnaireBtn, salBtn, sleepBtn)
    return column


def get_mainMenu(event):
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
    physBtn.on_click(startPipeline)
    sleepBtn = pn.widgets.Button(
        name="Sleep Data",
        sizing_mode="stretch_width",
        align="end",
        button_type="primary",
    )
    sleepBtn.on_click(startPipeline)
    questionnaireBtn = pn.widgets.Button(
        name="Questionnaire Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    questionnaireBtn.on_click(startPipeline)
    psychBtn = pn.widgets.Button(
        name="Psychological Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    psychBtn.on_click(startPipeline)
    salBtn = pn.widgets.Button(
        name="Saliva Data",
        sizing_mode="stretch_width",
        button_type="primary",
    )
    salBtn.on_click(startPipeline)
    if os.path.exists("./assets/Icons/"):
        pathToIcons = "./assets/Icons/"
    elif os.path.exists("../assets/Icons/"):
        pathToIcons = "../assets/Icons/"
    else:
        pathToIcons = "../../assets/Icons/"
    iconNames = [
        "Physiological.svg",
        "Psychological.svg",
        "Questionnaire.svg",
        "Saliva.svg",
        "Sleep.svg",
    ]
    physCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[0],
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
    psychCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[1],
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
    questionnaireCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[2],
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
    salCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[3],
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
    sleepCard = pn.GridBox(
        pn.pane.SVG(
            pathToIcons + iconNames[4],
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
    signalSelection = pn.GridBox(
        *[physCard, psychCard, questionnaireCard, salCard, sleepCard],
        ncols=3,
        nrows=2,
        max_width=1000,
        height=600,
    )
    pane = pn.Column(pn.pane.Markdown(fileString), signalSelection)
    if len(app.main) > 0:
        app.main[0].objects = [pane]
    else:
        app.main.append(pane)


pn.config.console_output = "disable"
app.sidebar.append(get_sidebar())
get_mainMenu(None)
app.servable()
