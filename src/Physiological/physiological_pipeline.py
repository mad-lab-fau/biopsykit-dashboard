import panel as pn

from src.Physiological.download_results import DownloadResults
from src.Physiological.relative_band_energy import FrequencyBands
from src.Physiological.rsp_settings import SetRspParameters
from src.Physiological.select_cft_sheet import SelectCFTSheet
from src.Physiological.sessions import Session
from src.Physiological.recordings import Recordings
from src.Physiological.compress_files import Compress
from src.Physiological.add_times import AskToAddTimes, AddTimes
from src.Physiological.file_upload import FileUpload
from src.Physiological.data_arrived import DataArrived
from src.Physiological.outlier_detection import OutlierDetection, AskToDetectOutliers
from src.Physiological.processing_and_preview import (
    ProcessingAndPreview,
    ProcessingPreStep,
)
from src.Physiological.process_hrv import SetHRVParameters, AskToProcessHRV
from src.Physiological.signal_type import PhysSignalType


class PhysiologicalPipeline:
    pipeline = None
    name = "Physiological"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True, inherit_params=True)

        self.pipeline.add_stage(
            "Select Physiological Session Type",
            PhysSignalType(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage("Sessions", Session())
        self.pipeline.add_stage(
            "Recordings",
            Recordings(),
            **{
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage("Multiple Files", Compress())
        self.pipeline.add_stage(
            "Upload Files",
            FileUpload(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Data arrived",
            DataArrived(),
            **{"ready_parameter": "proceed", "next_parameter": "next_page"},
        )
        self.pipeline.add_stage("Set RSP Parameters", SetRspParameters())
        self.pipeline.add_stage(
            "Select CFT Sheet",
            SelectCFTSheet(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Do you want to add time logs?",
            AskToAddTimes(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage(
            "Add Times",
            AddTimes(),
            **{"next_parameter": "next"},
        )
        self.pipeline.add_stage(
            "Frequency Bands",
            FrequencyBands(),
            **{"next_parameter": "next"},
        )
        self.pipeline.add_stage(
            "Do you want to detect Outlier?",
            AskToDetectOutliers(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next",
            },
        )
        self.pipeline.add_stage("Expert Outlier Detection", OutlierDetection())
        self.pipeline.add_stage(
            "Do you want to process the HRV also?",
            AskToProcessHRV(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Now the Files will be processed",
            ProcessingPreStep(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
            },
        )

        self.pipeline.add_stage("Set HRV Parameters", SetHRVParameters())
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage("Results", DownloadResults())
        self.pipeline.define_graph(
            {
                "Select Physiological Session Type": "Sessions",
                "Sessions": "Recordings",
                "Recordings": ("Multiple Files", "Upload Files"),
                "Multiple Files": "Upload Files",
                "Upload Files": "Data arrived",
                "Data arrived": (
                    "Do you want to add time logs?",
                    "Select CFT Sheet",
                    "Set RSP Parameters",
                ),
                "Set RSP Parameters": "Now the Files will be processed",
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
