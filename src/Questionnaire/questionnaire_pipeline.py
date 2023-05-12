import panel as pn

from src.Questionnaire.check_selected_questionnaires import CheckSelectedQuestionnaires
from src.Questionnaire.load_data import LoadQuestionnaireData
from src.Questionnaire.loading_parameters import (
    AskToSetLoadingParameters,
    SetLoadingParametersExpert,
)
from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from src.Questionnaire.show_results import ShowResults

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")

# TODO: Convert Scores into long Format, Convert Questionnaire Items
class QuestionnairePipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage(
            "Ask for additional parameters",
            AskToSetLoadingParameters(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Set Loading Parameters", SetLoadingParametersExpert())
        self.pipeline.add_stage(
            "Upload Questionnaire Data",
            LoadQuestionnaireData(),
            ready_parameter="ready",
        )
        self.pipeline.add_stage("Set Questionnaires", SuggestQuestionnaireScores())
        self.pipeline.add_stage(
            "Check selected Questionnaires", CheckSelectedQuestionnaires()
        )
        self.pipeline.add_stage("Show Results", ShowResults())

        self.pipeline.define_graph(
            {
                "Ask for additional parameters": (
                    "Set Loading Parameters",
                    "Upload Questionnaire Data",
                ),
                "Set Loading Parameters": "Upload Questionnaire Data",
                "Upload Questionnaire Data": "Set Questionnaires",
                "Set Questionnaires": "Check selected Questionnaires",
                "Check selected Questionnaires": "Show Results",
            }
        )
