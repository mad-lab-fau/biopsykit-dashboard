import panel as pn

from src.under_construction_page import UnderConstruction


class PsychologicalPipeline:
    pipeline = None
    name = "Psychological Data"
    icon_svg = "https://tabler-icons.io/static/tabler-icons/icons/brain.svg"
    icon_name = "brain"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(
            debug=True,
        )

        # self.pipeline.add_stage("Test", TestPage(), ready_parameter="ready")
        self.pipeline.add_stage(
            "Under Construction",
            UnderConstruction(),
            ready_parameter="ready",
        )
        # self.pipeline.add_stage("Set up Study Design", SetUpStudyDesign())

        # self.pipeline.add_stage(
        #     "Ask for Subject Condition List",
        #     AskToLoadConditionList(),
        #     ready_parameter="ready",
        #     next_parameter="next_page",
        #     auto_advance=True,
        # )

        # self.pipeline.define_graph(
        #     {
        #         "Ask for Recording Device": "Set Parsing Parameters",
        #         "Set Parsing Parameters": "Ask for Format",
        #         "Ask for Format": "Upload Sleep Data",
        #     }
        # )
