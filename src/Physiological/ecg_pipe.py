import panel as pn

from src.Physiological.choose_subtypes import ChooseSubtypes
from src.Physiological.select_times import SelectTimes
from src.Physiological.session_kind import SessionKind
from src.Physiological.file_upload import FileUpload
from src.Physiological.data_arrived import DataArrived
from src.Physiological.trim_session import TrimSession
from src.Physiological.outlier_detection import OutlierDetection
from src.Physiological.processing_and_preview import ProcessingAndPreview
from src.Physiological.process_hrv import ProcessHRV

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


# TODO: Welche Subtypen (Ankreuzfelder), Finish + Results runterladen (DF HR und HV + Plots optional auch, als .zip File), OutlierDetection nur wenn es ecg ist
class ECGPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage(
            "Session Kind",
            SessionKind,
            ready_parameter="ready",
            show_header=False,
        )
        self.pipeline.add_stage("Upload File", FileUpload, ready_parameter="ready")
        self.pipeline.add_stage("Data arrived", DataArrived(), ready_parameter="ready")
        self.pipeline.add_stage("Trim Session", TrimSession())
        self.pipeline.add_stage("Outlier Processing", OutlierDetection())
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage("Process HRV", ProcessHRV())
        self.pipeline.add_stage("Select Subtypes", ChooseSubtypes)

        self.pipeline.define_graph(
            {
                "Session Kind": "Upload File",
                "Upload File": "Data arrived",
                "Data arrived": "Trim Session",
                "Trim Session": "Outlier Processing",
                "Outlier Processing": "Preview",
                "Preview": "Process HRV",
                "Process HRV": "Select Subtypes",
            }
        )

        # self.pipeline.layout = pn.Column(
        #     pn.Row(
        #         self.pipeline.title,
        #         pn.layout.HSpacer(),
        #         self.pipeline.prev_button,
        #         self.pipeline.next_button,
        #     ),
        #     self.pipeline.network,
        #     self.pipeline.stage,
        # )
