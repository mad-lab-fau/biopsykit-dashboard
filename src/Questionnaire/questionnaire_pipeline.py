import panel as pn

from src.Questionnaire.check_selected_questionnaires import CheckSelectedQuestionnaires
from src.Questionnaire.convert_scale import AskToConvertScales, ConvertScales
from src.Questionnaire.crop_scale import AskToCropScale, CropScales
from src.Questionnaire.invert_scores import AskToInvertScores, InvertScores
from src.Questionnaire.load_data import LoadQuestionnaireData
from src.Questionnaire.loading_parameters import (
    AskToSetLoadingParameters,
    SetLoadingParametersExpert,
)
from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from src.Questionnaire.show_results import ShowResults
from src.Questionnaire.wide_to_long import AskToChangeFormat, ConvertToLong

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")

# TODO: Convert Scores into long Format
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
        self.pipeline.add_stage(
            "Ask to convert scales",
            AskToConvertScales(),
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )

        self.pipeline.add_stage("Convert Scales", ConvertScales())

        self.pipeline.add_stage(
            "Ask To crop scales",
            AskToCropScale(),
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )

        self.pipeline.add_stage("Crop Scales", CropScales())

        self.pipeline.add_stage(
            "Ask to invert scores",
            AskToInvertScores(),
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )

        self.pipeline.add_stage("Invert scores", InvertScores())
        self.pipeline.add_stage("Show Results", ShowResults())
        self.pipeline.add_stage(
            "Ask to change format",
            AskToChangeFormat,
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )
        self.pipeline.add_stage("Change format", ConvertToLong())

        self.pipeline.define_graph(
            {
                "Ask for additional parameters": (
                    "Set Loading Parameters",
                    "Upload Questionnaire Data",
                ),
                "Set Loading Parameters": "Upload Questionnaire Data",
                "Upload Questionnaire Data": "Set Questionnaires",
                "Set Questionnaires": "Check selected Questionnaires",
                "Check selected Questionnaires": "Ask to convert scales",
                "Ask to convert scales": ("Convert Scales", "Ask To crop scales"),
                "Convert Scales": "Ask To crop scales",
                "Ask To crop scales": ("Crop Scales", "Ask to invert scores"),
                "Crop Scales": "Ask to invert scores",
                "Ask to invert scores": (
                    "Invert scores",
                    "Ask to change format",
                    "Show Results",
                ),
                "Ask to change format": ("Show Results", "Change format"),
                "Change format": "Show Results",
                "Invert scores": "Show Results",
            }
        )
