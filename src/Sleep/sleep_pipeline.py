import panel as pn

from src.Sleep.choose_device import ChooseRecordingDevice
from src.Sleep.choose_file_or_folder import ZipFolder
from src.Sleep.upload_parameters import SetSleepDataParameters
from src.Sleep.upload_sleep_data import UploadSleepData

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class SleepPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(
            debug=True,
        )

        self.pipeline.add_stage("Set Parsing Parameters", SetSleepDataParameters())

        self.pipeline.add_stage(
            "Ask for Recording Device", ChooseRecordingDevice(), ready_parameter="ready"
        )

        self.pipeline.add_stage("Ask for Format", ZipFolder())

        self.pipeline.add_stage(
            "Upload Sleep Data", UploadSleepData(), ready_parameter="ready"
        )

        # self.pipeline.add_stage(
        #     "Ask for Subject Condition List",
        #     AskToLoadConditionList(),
        #     ready_parameter="ready",
        #     next_parameter="next_page",
        #     auto_advance=True,
        # )

        self.pipeline.define_graph(
            {
                "Ask for Recording Device": "Set Parsing Parameters",
                "Set Parsing Parameters": "Ask for Format",
                "Ask for Format": "Upload Sleep Data",
            }
        )