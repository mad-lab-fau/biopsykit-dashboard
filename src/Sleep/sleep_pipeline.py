import panel as pn

from src.Sleep.choose_device import ChooseRecordingDevice
from src.Sleep.choose_file_or_folder import ZipFolder
from src.Sleep.condition_list_sleep import (
    AskToLoadSleepConditionList,
    AddSleepConditionList,
)
from src.Sleep.download_sleep_results import DownloadSleepResults
from src.Sleep.process_sleep_data import ProcessDataParameters
from src.Sleep.results_preview import ResultsPreview
from src.Sleep.set_sleep_data_parameters import SetSleepDataParameters
from src.Sleep.upload_sleep_data import UploadSleepData


class SleepPipeline:
    name = "Sleep"
    icon_svg = "https://tabler-icons.io/static/tabler-icons/icons/bed.svg"
    icon_name = "bed"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline()
        self.pipeline.add_stage(
            "Ask for Recording Device",
            ChooseRecordingDevice(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage(
            "Set Parsing Parameters",
            SetSleepDataParameters(),
        )

        self.pipeline.add_stage("Ask for Format", ZipFolder())

        self.pipeline.add_stage(
            "Upload Sleep Data",
            UploadSleepData(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )

        self.pipeline.add_stage(
            "Ask for Subject Condition List",
            AskToLoadSleepConditionList(),
            ready_parameter="ready",
            next_parameter="next_page",
            auto_advance=True,
        )

        self.pipeline.add_stage(
            "Upload Subject Condition List",
            AddSleepConditionList(),
            ready_parameter="ready",
        )

        self.pipeline.add_stage("Process Data Parameters", ProcessDataParameters())

        self.pipeline.add_stage("Results Preview", ResultsPreview())

        self.pipeline.add_stage("Download Results", DownloadSleepResults())

        self.pipeline.define_graph(
            {
                "Ask for Recording Device": "Set Parsing Parameters",
                "Set Parsing Parameters": "Ask for Format",
                "Ask for Format": "Upload Sleep Data",
                "Upload Sleep Data": "Ask for Subject Condition List",
                "Ask for Subject Condition List": (
                    "Upload Subject Condition List",
                    "Process Data Parameters",
                ),
                "Upload Subject Condition List": "Process Data Parameters",
                "Process Data Parameters": "Results Preview",
                "Results Preview": "Download Results",
            }
        )
