SLEEP_MAX_STEPS = 7

POSSIBLE_DEVICES = [
    "Polysomnography",
    "Other IMU Device",
    "Withings",
]


UPLOAD_PARAMETERS_TEXT = (
    "# Set sleep data parameters \n\n "
    "Below you can set the parameters for the sleep data. "
    "If you are unsure, you can leave the default values."
)
CHOOSE_DEVICE_TEXT = (
    "# Choose the recording device \n\n "
    "Below you can choose the device you used to record your sleep data. "
    "If you used a different device, please choose 'Other IMU Device'."
)
ZIP_OR_FOLDER_TEXT = (
    "# File or Folder? \n\n "
    "If you want to upload a complete folder, please zip it first. "
    "You can then upload the zip file in the following step."
)
UPLOAD_SLEEP_DATA_TEXT = (
    "# Upload your sleep data \n\n "
    "Please upload your sleep data in the following step. "
    "You can either upload a single file or a zip file containing all your files. "
    "Following file formats are supported: .csv, .zip, .edf, .bin ."
)
ASK_TO_LOAD_CONDITION_LIST_SLEEP_TEXT = (
    "# Add a condition list \n\n"
    'If you want to add a condition list, click on the "Yes" button. Otherwise click on the "No" button. '
)
ADD_CONDITION_LIST_SLEEP_TEXT = (
    "# Add a condition list \n\n "
    "Below you can upload a condition list. This file has to be a .csv file or an "
    "Excel file."
)
DOWNLOAD_SLEEP_RESULTS_TEXT = "# Results \n\n Here you can download the results of your data. Just click on the button below."
