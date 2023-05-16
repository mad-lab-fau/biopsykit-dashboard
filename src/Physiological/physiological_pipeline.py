import panel as pn

from src.Physiological.download_results import DownloadResults
from src.Physiological.relative_band_energy import FrequencyBands
from src.Physiological.select_cft_sheet import SelectCFTSheet
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
from src.Physiological.process_hrv import SetHRVParameters, AskToProcessHRV
from src.Physiological.signal_type import PhysSignalType

pn.extension(sizing_mode="stretch_width")
pn.extension(notifications=True)
pn.extension("plotly", "tabulator")
pn.extension("katex")

# TODO: Bug fixing in add_times, Stage Results Preview und Download Files ergänzen; Funktionalität: Code Datei erzeugen
class PhysiologicalPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)

        self.pipeline.add_stage(
            "Select Physiological Session Type",
            PhysSignalType(),
            ready_parameter="ready",
            auto_advance=True,
        )
        self.pipeline.add_stage("Sessions", Session(), ready_parameter="ready")
        self.pipeline.add_stage(
            "Recordings", Recordings(), ready_parameter="ready", next_parameter="next"
        )
        self.pipeline.add_stage("Multiple Files", Compress())
        self.pipeline.add_stage("Upload Files", FileUpload(), ready_parameter="ready")
        self.pipeline.add_stage("Data arrived", DataArrived(), next_parameter="next")
        self.pipeline.add_stage(
            "Select CFT Sheet", SelectCFTSheet(), ready_parameter="ready"
        )
        self.pipeline.add_stage(
            "Do you want to add time logs?",
            AskToAddTimes(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Add Times", AddTimes(), next_parameter="next")
        self.pipeline.add_stage(
            "Frequency Bands", FrequencyBands(), next_parameter="next"
        )
        self.pipeline.add_stage(
            "Do you want to detect Outlier?",
            AskToDetectOutliers(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next",
        )
        self.pipeline.add_stage("Expert Outlier Detection", OutlierDetection())
        self.pipeline.add_stage(
            "Do you want to process the HRV also?",
            AskToProcessHRV(),
            auto_advance=True,
            ready_parameter="ready",
            next_parameter="next_page",
        )
        self.pipeline.add_stage(
            "Now the Files will be processed", ProcessingPreStep(), auto_advance=True
        )

        self.pipeline.add_stage("Set HRV Parameters", SetHRVParameters())
        # TODO: ResultsPreview wird zu Download Results
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage("Results", DownloadResults())
        self.pipeline.define_graph(
            {
                "Select Physiological Session Type": "Sessions",
                "Sessions": "Recordings",
                "Recordings": ("Multiple Files", "Upload Files"),
                "Multiple Files": "Upload Files",
                "Upload Files": "Data arrived",
                "Data arrived": ("Do you want to add time logs?", "Select CFT Sheet"),
                "Select CFT Sheet": "Now the Files will be processed",
                "Do you want to add time logs?": (
                    "Add Times",
                    "Do you want to detect Outlier?",
                    "Frequency Bands",
                ),
                "Frequency Bands": "Now the Files will be processed",
                "Add Times": ("Do you want to detect Outlier?", "Frequency Bands"),
                "Do you want to detect Outlier?": (
                    "Expert Outlier Detection",
                    "Do you want to process the HRV also?",
                ),
                "Expert Outlier Detection": "Do you want to process the HRV also?",
                "Do you want to process the HRV also?": (
                    "Set HRV Parameters",
                    "Now the Files will be processed",
                ),
                "Set HRV Parameters": "Now the Files will be processed",
                "Now the Files will be processed": "Preview",
                "Preview": "Results",
            }
        )