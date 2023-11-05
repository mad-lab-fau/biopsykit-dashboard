import os

os.environ["OUTDATED_IGNORE"] = "1"
import panel as pn

## This is the code that is used to generate the dashboard
pipeline = None

pn.extension(sizing_mode="stretch_width")
pn.extension(
    "plotly",
    sizing_mode="stretch_width",
)
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")

app = pn.template.BootstrapTemplate(
    title=f"BioPysKit Dashboard - {pipeline.name} ",
    header_background="#186FEF",
    logo="./assets/Icons/biopsykit_Icon.png",
    collapsed_sidebar=True,
)

app.config.console_output = "disable"
app.config.log_level = "CRITICAL"
app.sidebar.constant = False
app.main.constant = False
app.theme_toggle = False
info_btn = pn.widgets.Button(button_type="light", icon="help-hexagon", width=15)
info_btn.js_on_click(
    args={
        "target": "https://shmeske.github.io/biopsykit-dashboard-documentation/general-info.html"
    },
    code="window.open(target)",
)
app.header.append(info_btn)

app.main.append(
    pn.Column(
        pn.Row(
            pn.layout.HSpacer(),
            pipeline.pipeline.prev_button,
            pipeline.pipeline.next_button,
        ),
        pipeline.pipeline.stage,
        min_height=2000,
    )
)
app.servable()
