import panel as pn


from src.Saliva.ask_for_format import AskForFormat
from src.Saliva.condition_list import AskToLoadConditionList, AddConditionList
from src.Saliva.load_saliva_data import (
    LoadSalivaData,
)
from src.Saliva.saliva_features import ShowSalivaFeatures

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class SalivaPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline()
        self.pipeline.add_stage(
            "Ask for Format",
            AskForFormat(),
            ready_parameter="ready",
            auto_advance=True,
        )
        self.pipeline.add_stage(
            "Ask for Subject Condition List",
            AskToLoadConditionList(),
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )
        self.pipeline.add_stage(
            "Add Condition List",
            AddConditionList(),
            ready_parameter="ready",
        )
        self.pipeline.add_stage(
            "Load Saliva Data",
            LoadSalivaData(),
        )
        self.pipeline.add_stage("Show Features", ShowSalivaFeatures())

        self.pipeline.define_graph(
            {
                "Ask for Format": "Ask for Subject Condition List",
                "Ask for Subject Condition List": (
                    "Add Condition List",
                    "Load Saliva Data",
                ),
                "Add Condition List": "Load Saliva Data",
                "Load Saliva Data": "Show Features",
            }
        )
