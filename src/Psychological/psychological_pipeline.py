import panel as pn

from src.Psychological.setup_study import SetUpStudyDesign


class PsychologicalPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(
            debug=True,
        )

        # self.pipeline.add_stage("Test", TestPage(), ready_parameter="ready")
        self.pipeline.add_stage("Set upt Study Design", SetUpStudyDesign())

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
