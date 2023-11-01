import pytz

PHYSIOLOGICAL_MAX_STEPS = 12
PHYSIOLOGICAL_SIGNAL_OPTIONS = ["", "ECG", "RSP", "EEG"]
TIMEZONES = ["None Selected"] + list(pytz.all_timezones)
PHYSIOLOGICAL_HW_OPTIONS = ["NilsPod", "BioPac"]

HRV_METHODS = ["hrv_time", "hrv_nonlinear", "hrv_frequency"]

OUTLIER_METHODS = [
    "quality",
    "artifact",
    "physiological",
    "statistical_rr",
    "statistical_rr_diff",
]
EDR_TYPES = ["peak_trough_mean", "peak_trough_diff", "peak_peak_interval"]

SESSION_TEXT = (
    "# Number of Sessions \n"
    "In this step you can define if your data consists of a single Session or multiple Sessions. \n\n"
    "In this context a single Session is defined that only one Sensor is used, "
    "while multiple Sessions describe that two or more sensors are used. \n"
)

SIGNAL_TYPE_TEXT = "# Selecting Physiological Signal Type"
SELECT_CFT_TEXT = (
    "# Select CFT Sheet \n\n"
    "This step allows you to select a CFT sheet from a list "
    "of available sheets."
)

SELECT_FREQUENCY_TEXT = (
    "# Set Frequency Bands"
    "In this step you can set the frequency bands for the analysis. "
    "The default values are the standard frequency bands for EEG analysis. "
    "You can change the values by clicking on the text field and entering the desired value. "
    "The values are in Hz."
)

RECORDINGS_TEXT = (
    "# Number of Recordings \n"
    "After you defined the kind of Sessions, in this step you will set if your data"
    "consists of a single Recording or multiple recordings.\n\n"
    "A single Recording means, that you only have one file per subject and multiple Recording"
    "is defined as two or more files per subject. \n"
)
PROCESSING_PREVIEW_TEXT = (
    "# Preview of the Results \n \n"
    "Below you can find a short summary of the analyzed data "
    "(Preview of the Dataframe, and several statistical values)."
)
PROCESS_HRV_TEXT = (
    "# Processing HRV \n \n"
    "If you want to additionally process the Heart Rate variability, "
    "you can select the matching parameters and then hit the "
    "process button, and then proceed. Otherwise, you can skip "
    "this step and go to the next stage. "
)
ASK_PROCESS_HRV_TEXT = (
    "# Processing HRV \n \n"
    "If you want to additionally process the Heart Rate variability, "
    "you can select the matching parameters and then "
    "hit the process button, and then proceed. "
    "Otherwise, you can skip this step and go to the next stage. \n \n"
)
ASK_DETECT_OUTLIER_TEXT = "# Do you want to check for outliers?"

OUTLIER_DETECTION_TEXT = (
    "# Outlier Detection \n\n"
    "# # In this stage the ECG signal will be processed. This will be done in three steps: "
    "Filtering, R-peak detection, Outlier correction. \n\n"
    "Below you can select the outlier correction methods, which consist of: \n"
    "- Correlation: Computes cross-correlation coefficient between every single beat and the average of all"
    " detected beats. Marks beats as outlier if cross-correlation coefficient is below a certain threshold. \n"
    "- Quality: Uses the ECG_Quality indicator is below a certain threshold. \n"
    "- Artifact: Artifact detection based on Berntson et al. (1990)."
    "- Physiological: Physiological outlier removal. "
    "Marks beats if their heart rate is above or below a threshold that "
    "is very unlikely to be achieved physiologically. \n"
    "- Statistical rr: Marks beats as outlier if the RR interval is above or below a certain threshold. \n"
    "Statistical outlier removal based on RR intervals. Marks beats as outlier if the "
    "intervals are within the xx% highest or lowest values. Values are removed based on the z-score; "
    "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); "
    "2.576 => 1% (0.5% highest, 0.5% lowest values). \n"
    "- Statistical rr diff: Statistical outlier removal based on successive differences "
    "of RR intervals. Marks beats as outlier if the difference of successive RR intervals "
    "are within the xx% highest or lowest heart rates. Values are removed based on the z-score; "
    "e.g. 1.96 => 5% (2.5% highest, 2.5% lowest values); 2.576 => 1% "
    "(0.5% highest, 0.5% lowest values). \n"
    "Furthermore, you can set the parameters for the outlier detection methods you chose down below. "
    "If you don't change anything the default values for the corresponding method will be used. \n"
)

FILE_UPLOAD_TEXT = (
    "# Upload your session File \n"
    "## The supported File formats are .bin, .csv, and you can also choose Folders.\n"
    "After your upload your file will also be checked if it contains the necessary columns.\n"
)

DOWNLOAD_RESULT_TEXT = "# Download Result \n"
DATA_ARRIVED_TEXT = (
    "# Files uploaded successfully \n"
    "Below is a short summary of the files which you uploaded."
    "These files can be further analysed in the following steps."
)

COMPRESS_FILES_TEXT = (
    "# Compress your Files\n"
    "Because you selected, that you want to analyse more than one File,"
    "you have to compress the content of your Folder into one .zip File.\n"
    "Please do that before proceeding to the next step.\n"
)
ASK_ADD_TIMES_TEXT = (
    "# Do you want to add Phases for your Data?\n"
    "If you want to upload an Excel oder CSV File, or if you want to manually add Phases "
    "to your data then click on the Add Times Button otherwise skip"
)
ADD_TIMES_TEXT = "# Select Times"
PRESTEP_PROCESSING_TEXT = (
    "# Processing \n"
    "Im nächsten Schritt werden die Daten verarbeitet, dieser Schritt dauert einen Moment :)."
)

SET_RSP_PARAMETERS_TEXT = (
    "# RSP Parameters\n"
    "Here you can set the different parameters for the RSP analysis. You may select if the data is "
    "a Raw respiration signal or if it has to be estimated by the ECG. \n"
    "You ma also choose the method used to estimate the respiration signal from the ECG. \n"
)
