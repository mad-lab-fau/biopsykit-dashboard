import panel as pn

from src.Physiological.TestStage import TestInput
from src.Physiological.result_preview import ResultsPreview
from src.Physiological.sessions import Session
from src.Physiological.recordings import Recordings
from src.Physiological.compress_files import Compress
from src.Physiological.add_times import AddTimes, AskToAddTimes
from src.Physiological.file_upload import FileUpload
from src.Physiological.data_arrived import DataArrived
from src.Physiological.outlier_detection import OutlierDetection, AskToDetectOutliers
from src.Physiological.processing_and_preview import (
    ProcessingAndPreview,
    ProcessingPreStep,
)
from src.Physiological.process_hrv import ProcessHRV, AskToProcessHRV

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")

# TODO: Bug fixing in add_times, Stage Results Preview und Download Files ergänzen; Funktionalität: Code Datei erzeugen
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
            "Do you want to add time logs?",
            AskToAddTimes(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Add Times", AddTimes(), ready_parameter="ready")
        self.pipeline.add_stage(
            "Do you want to detect Outlier?",
            AskToDetectOutliers(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Expert Processing", OutlierDetection())
        self.pipeline.add_stage(
            "Now the Files will be processed", ProcessingPreStep(), auto_advance=True
        )

        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage(
            "Do you want to process the HRV also?",
            AskToProcessHRV(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next_page",
        )
        self.pipeline.add_stage("Process HRV", ProcessHRV())
        self.pipeline.add_stage("Results", ResultsPreview())

        self.pipeline.define_graph(
            {
                "Sessions": "Recordings",
                "Recordings": ("Multiple Files", "Upload Files"),
                "Multiple Files": "Upload Files",
                "Upload Files": "Data arrived",
                "Data arrived": "Do you want to add time logs?",
                "Do you want to add time logs?": (
                    "Add Times",
                    "Do you want to detect Outlier?",
                ),
                "Add Times": "Do you want to detect Outlier?",
                "Do you want to detect Outlier?": (
                    "Expert Processing",
                    "Now the Files will be processed",
                ),
                "Now the Files will be processed": "Preview",
                "Expert Processing": "Now the Files will be processed",
                "Now the Files will be processed": "Preview",
                "Preview": "Do you want to process the HRV also?",
                "Do you want to process the HRV also?": (
                    "Process HRV",
                    "Results",
                ),
                "Process HRV": "Results",
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
