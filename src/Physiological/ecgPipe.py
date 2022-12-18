import panel as pn
from src.Physiological.sessionKind import SessionKind
from src.Physiological.fileUpload import FileUploadPhysiological
from src.Physiological.dataArrived import DataArrived
from src.Physiological.trimSession import TrimSession
from src.Physiological.outlierDetection import OutlierDetection
from src.Physiological.processingAndPreview import ProcessingAndPreview
from src.Physiological.processHRV import ProcessHRV
pn.extension(sizing_mode='stretch_width')
pn.extension(notifications=True)
pn.extension('plotly', 'tabulator')
pn.extension('katex')


# TODO: Welche Subtypen (Ankreuzfelder), Finish + Results runterladen (DF HR und HV + Plots optional auch, als .zip File)
class ECGPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage("Session Kind", SessionKind(), ready_parameter='ready')
        self.pipeline.add_stage("File Upload", FileUploadPhysiological(), ready_parameter='ready')
        self.pipeline.add_stage("Data arrived", DataArrived(), ready_parameter='ready')
        self.pipeline.add_stage("Trim Session", TrimSession())
        self.pipeline.add_stage("Outlier Processing", OutlierDetection())
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage('Process HRV', ProcessHRV())
