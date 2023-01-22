import panel as pn
from src.Physiological.sessions import Session
from src.Physiological.recordings import Recordings
from src.Physiological.compress_files import Compress
from src.Physiological.add_times import AddTimes, AskToAddTimes
from src.Physiological.choose_subtypes import ChooseSubtypes
from src.Physiological.select_times import SelectTimes
from src.Physiological.session_kind import SessionKind
from src.Physiological.file_upload import FileUpload
from src.Physiological.data_arrived import DataArrived
from src.Physiological.trim_session import TrimSession
from src.Physiological.outlier_detection import OutlierDetection, AskToDetectOutliers
from src.Physiological.processing_and_preview import ProcessingAndPreview
from src.Physiological.process_hrv import ProcessHRV

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")


class ECGPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)

        self.pipeline.add_stage("Sessions", Session(), ready_parameter="ready")
        self.pipeline.add_stage(
            "Recordings", Recordings(), ready_parameter="ready", next_parameter="next"
        )
        self.pipeline.add_stage("Multiple Files", Compress())
        self.pipeline.add_stage("Upload Files", FileUpload(), ready_parameter="ready")
        self.pipeline.add_stage("Data arrived", DataArrived())
        self.pipeline.add_stage(
            "Want to add Times?",
            AskToAddTimes(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Add Times", AddTimes())
        self.pipeline.add_stage(
            "Do you want to detect Outlier?",
            AskToDetectOutliers(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Expert Processing", OutlierDetection())
        # self.pipeline.add_stage("Now the Files will be processed")

        self.pipeline.define_graph(
            {
                "Sessions": "Recordings",
                "Recordings": ("Multiple Files", "Upload Files"),
                "Multiple Files": "Upload Files",
                "Upload Files": "Data arrived",
                "Data arrived": "Want to add Times?",
                "Want to add Times?": ("Add Times", "Do you want to detect Outlier?"),
                "Add Times": "Do you want to detect Outlier?",
                "Do you want to detect Outlier?": (
                    "Expert Processing",
                    "Now the Files will be processed",
                ),
                "Expert Processing": "Now the Files will be processed",
                # "Now the Files will be processed": "Preview",
                # "Preview": "Do you want to process the HRV also?",
                # "Do you want to process the HRV also?": ("Process HRV", "Results"),
                # "Process HRV": "Results"
                # Vorher noch fragen ob man das überhaupt will
                # Zeiten hochladen oder eintragen
                # Hier nun fragen, ob die Daten korrigiert werden sollen (Nein, Default, Expert Mode)
                # Sollen die Daten getrimmt werden?
                # Preview
                # Soll noch HRV? berechnet werden
                #
            }
        )

        # self.pipeline.add_stage(
        #     "Session Kind",
        #     SessionKind,
        #     ready_parameter="ready",
        #     show_header=False,
        # )
        # self.pipeline.add_stage("Upload File", FileUpload, ready_parameter="ready")
        # self.pipeline.add_stage("Data arrived", DataArrived(), ready_parameter="ready")
        # self.pipeline.add_stage("Trim Session", TrimSession())
        # self.pipeline.add_stage("Outlier Processing", OutlierDetection())
        # self.pipeline.add_stage("Preview", ProcessingAndPreview())
        # self.pipeline.add_stage("Process HRV", ProcessHRV())
        # self.pipeline.add_stage("Select Subtypes", ChooseSubtypes)

        # self.pipeline.define_graph(
        #     {
        #         "Session Kind": "Upload File",
        #         "Upload File": "Data arrived",
        #         "Data arrived": "Trim Session",
        #         "Trim Session": "Outlier Processing",
        #         "Outlier Processing": "Preview",
        #         "Preview": "Process HRV",
        #         "Process HRV": "Select Subtypes",
        #     }
        # )
