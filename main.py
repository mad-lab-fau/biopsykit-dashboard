import os

os.environ["OUTDATED_IGNORE"] = "1"
import panel as pn


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
current_page = MainPage(app)
pn.config.notifications = True
pn.config.console_output = "disable"
app.sidebar.append(current_page.get_sidebar())
current_page.get_main_menu(None)
app.servable()
