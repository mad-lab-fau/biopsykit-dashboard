import panel as pn

from src.Questionnaire.check_selected_questionnaires import CheckSelectedQuestionnaires
from src.Questionnaire.convert_scale import AskToConvertScales, ConvertScales
from src.Questionnaire.crop_scale import AskToCropScale, CropScales
from src.Questionnaire.download_results import DownloadQuestionnaireResults
from src.Questionnaire.invert_scores import AskToInvertScores, InvertScores
from src.Questionnaire.loading_parameters import (
    AskToSetLoadingParameters,
    SetLoadingParametersManually,
)
from src.Questionnaire.select_scores import SuggestQuestionnaireScores
from src.Questionnaire.show_results import ShowResults
from src.Questionnaire.upload_questionnaire_data import UploadQuestionnaireData
from src.Questionnaire.wide_to_long import AskToChangeFormat, ConvertToLong


class QuestionnairePipeline:
    pipeline = None
    name = "Questionnaire"
    icon_svg = "https://tabler-icons.io/static/tabler-icons/icons/clipboard-check.svg"
    icon_name = "clipboard-check"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True, inherit_params=True)
        self.pipeline.add_stage(
            "Ask for additional parameters",
            AskToSetLoadingParameters(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage(
            "Set Loading Parameters", SetLoadingParametersManually()
        )
        self.pipeline.add_stage(
            "Upload Questionnaire Data",
            UploadQuestionnaireData(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
            },
        )
        self.pipeline.add_stage("Set Questionnaires", SuggestQuestionnaireScores())
        self.pipeline.add_stage(
            "Check selected Questionnaires", CheckSelectedQuestionnaires()
        )
        self.pipeline.add_stage(
            "Ask to convert scales",
            AskToConvertScales(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Convert Scales", ConvertScales())

        self.pipeline.add_stage(
            "Ask To crop scales",
            AskToCropScale(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Crop Scales", CropScales())

        self.pipeline.add_stage(
            "Ask to invert scores",
            AskToInvertScores(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )

        self.pipeline.add_stage("Invert scores", InvertScores())
        self.pipeline.add_stage(
            "Show Results",
            ShowResults(),
            **{
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Ask to change format",
            AskToChangeFormat(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage("Change format", ConvertToLong())

        self.pipeline.add_stage("Download Results", DownloadQuestionnaireResults())

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
                    "Show Results",
                ),
                "Invert scores": "Show Results",
                "Show Results": ("Download Results", "Ask to change format"),
                "Ask to change format": ("Download Results", "Change format"),
                "Change format": "Download Results",
            }
        )
