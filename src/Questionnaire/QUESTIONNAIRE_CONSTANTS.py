QUESTIONNAIRE_MAX_STEPS = 9

ASK_TO_SET_LOADING_PARAMETERS_TEXT = (
    "# Loading Parameters \n\n "
    "If you want to explicitly set loading parameters such as: "
    "the Subject column, Condition column, etc. you can do so by clicking on the "
    '"Set Loading Parameters" button. '
    "This will take you to an additional step where you can set the loading parameters. "
    'Otherwise, click on "Default".'
)

LOAD_QUESTIONNAIRE_DATA_TEXT = (
    "# Set Loading Parameters \n\n"
    "In this step you may set the loading parameters which will be used . "
)

LOADING_DATA_TEXT = (
    "# Upload Questionnaire Data \n\n"
    "Here you can upload your Questionnaire Data. "
    "In the following steps you can select the different Scores you want to calculate, "
    "and also convert them as well as plot your data."
)

SUGGEST_QUESTIONNAIRE_SCORES_TEXT = (
    "# Select Scores to Calculate \n\n"
    "In this step you may select the scores you want to calculate. "
    "You may add the Questionnaire you want to be analyzed "
    "(e.g. Perceived Stress Scale) as well as the pattern "
    "of the corresponding columns, where you can select "
    "the start and end of the columns."
)

CHECK_SELECTED_QUESTIONNAIRES_TEXT = (
    "# Check selected questionnaires \n\n"
    "In this step you may check the selected questionnaires "
    "and the corresponding columns. If you want to check them "
    'press the "Check Questionnaires" button. '
    "Otherwise, you may continue with the next step "
    "in which the scores will be computed."
)

ASK_TO_CONVERT_SCALES_TEXT = (
    "# Do you want to convert the scales of the selected questionnaires?\n\n"
    "If you want to change the scales of the selected questionnaires, "
    'click on the "Yes" button. Otherwise, click on the "No" button to proceed.'
)

CONVERT_SCALES_TEXT = (
    "# Convert Scales \n\n"
    "In this step you can convert the scales of your data. You can either "
    "convert the score range of the selected questionnaires or alternatively just for "
    "the selected columns. "
)

ASK_TO_CROP_SCALE_TEXT = (
    "# Would you like to crop the scale(s) of your data? \n\n"
    "If you want to crop the scale(s) of your data, i.e., "
    "set values out of range to specific minimum and maximum values or to NaN. "
)

CROP_SCALES_TEXT = (
    "# Crop scales\n\n"
    "In this step you can crop the scales of your data. You can set the range of the scores below in "
    "the array input. Please be sure that you enter the data like this: [firstValue, secondValue, etc.]. "
    "You can also click on the checkbox to set the values out of range to NaN. "
)

ASK_TO_INVERT_SCORES_TEXT = (
    "# Do you want to invert the scores of selected column(s)?\n\n"
    "In many questionnaires some items need to be inverted (reversed) before sum scores can be computed. "
    "You can either skip this step or invert the scores of the selected columns in the following step."
)

INVERT_SCORES_TEXT = (
    "# Invert Scores \n\n"
    "In this step you can invert the scores of your data. You can set the range of the scores "
    "below in the Array Input. Please be sure that you enter the data like this: [firstValue, secondValue, etc.]. You can "
    "also select just specific columns to invert the scores. "
)

SHOW_RESULTS_TEXT = (
    "# Show Results \n\n"
    "In this step you can see the results of your data. If you want to change the format of your dataframes from the "
    "wide Format to the long Format you can do so by clicking on the next button on the top right. "
    'Otherwise, you can download the results by clicking on the "Download" button below the Datatable.'
)

ASK_TO_CHANGE_FORMAT_TEXT = (
    "# Do you want to change the format of your Dataframes? \n "
    'If wou want to divide the Data of your questionnaires into different subscales please click on "Yes" '
    "otherwise you may skip that step."
)

CHANGE_FORMAT_TEXT = (
    "# Convert from wide to long format \n "
    "In the wide-format dataframe, the index levels to be converted into long-format are expected to be encoded in the "
    "column names and separated by `_`. If multiple levels should be converted into long-format, e.g., for a "
    "questionnaire with subscales (level `subscale`) that was assessed pre and post (level `time`), then the different "
    "levels are all encoded into the string. The level order is specified by ``levels``."
    "Below you can select from the questionnaire(s) of the provided data in order to change the format."
    ' However only those questionnaire(s) which include column(s) that contain the symbol "_" are shown.'
)

DOWNLOAD_RESULTS_TEXT = "# Results \n\n Here you can download the results of your data. Just click on the button below."
