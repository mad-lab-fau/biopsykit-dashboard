import pandas as pd
import panel as pn
import param

from src.Saliva.SALIVA_CONSTANTS import LOAD_PLATE_DATA_TEXT
from src.Saliva.SalivaBase import SalivaBase
from src.utils import load_saliva_plate, load_saliva_wide_format


class LoadSalivaData(SalivaBase):
    ready = param.Boolean(default=False)
    temporary_dataframe = param.DataFrame(default=None)
    upload_btn = pn.widgets.FileInput(accept=".csv,.xls,.xlsx", multiple=False)
    saliva_selector = pn.widgets.Select(
        name="Choose the saliva type",
        options=["", "cortisol", "amylase"],
        visible=False,
    )
    select_subject_col = pn.widgets.Select(
        name="Select Subject Column", options=[], visible=False
    )
    select_condition_col = pn.widgets.Select(
        name="Select Condition Column", options=[], visible=False
    )
    select_additional_index_cols = pn.widgets.MultiChoice(
        name="Select Additional Index Columns",
        options=[],
        visible=False,
    )
    sample_times_input = pn.widgets.TextInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
        visible=False,
    )
    select_id_col_names = pn.widgets.MultiChoice(
        name="Select Id Columns",
        options=[],
        visible=False,
    )
    select_sample_id_col = pn.widgets.Select(
        name="Select Sample ID Column", options=[], visible=False
    )
    select_data_col = pn.widgets.Select(
        name="Select Data Column", options=[], visible=False
    )
    regex_input = pn.widgets.TextInput(
        name="Regex for sample id",
        value=None,
        placeholder="regular expression to extract subject ID, day ID and sample ID from the sample identifier",
        visible=False,
    )
    fill_condition_list = pn.widgets.Button(name="Set Condition List", visible=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOAD_PLATE_DATA_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(LOAD_PLATE_DATA_TEXT)
        self.saliva_selector.link(self, callbacks={"value": self.saliva_type_changed})
        self.upload_btn.link(self, callbacks={"value": self.parse_file_input})
        self._view = pn.Column(
            self.header,
            self.upload_btn,
            self.saliva_selector,
            self.get_wide_format_column(),
            self.get_plate_format_column(),
        )

    def switch_plate_format_visibility(self, visible: bool):
        self.select_sample_id_col.visible = visible
        self.select_data_col.visible = visible
        self.select_id_col_names.visible = visible
        self.regex_input.visible = visible
        self.sample_times_input.visible = visible
        self.fill_condition_list.visible = visible

    def switch_wide_format_visibility(self, visible: bool):
        self.select_subject_col.visible = visible
        self.select_condition_col.visible = visible
        self.select_additional_index_cols.visible = visible
        self.sample_times_input.visible = visible

    def get_plate_format_column(self) -> pn.Column:
        return pn.Column(
            self.select_sample_id_col,
            self.select_data_col,
            self.select_id_col_names,
            self.regex_input,
            self.sample_times_input,
            self.fill_condition_list,
        )

    def get_wide_format_column(self) -> pn.Column:
        return pn.Column(
            self.select_subject_col,
            self.select_condition_col,
            self.select_additional_index_cols,
            self.sample_times_input,
        )

    def saliva_type_changed(self, _, event):
        self.saliva_type = event.new
        if event.new == "":
            self.ready = False
        else:
            self.ready = True

    def parse_file_input(self, target, event):
        if ".csv" in self.upload_btn.filename:
            self.temporary_dataframe = self.handle_csv_file(self.upload_btn.value)
        elif ".xls" in self.upload_btn.filename:
            self.temporary_dataframe = self.handle_excel_file(self.upload_btn.value)
        if self.temporary_dataframe.empty:
            self.handle_error(ValueError("No data loaded"))
            return
        try:
            self.temporary_dataframe.dropna(axis=1, how="all", inplace=True)
            # self.show_param_input_plate()
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            self.handle_error(e)

    def handle_error(self, e: Exception):
        pn.state.notifications.error("Error while loading data: " + str(e))
        self.ready = False
        # self.hide_param_input()

    def handle_csv_file(self, file) -> pd.DataFrame:
        try:
            return pd.read_csv(file, skiprows=2)
        except Exception as e:
            self.handle_error(e)
            return pd.DataFrame()

    def handle_excel_file(self, file) -> pd.DataFrame:
        try:
            df = pd.read_excel(file, skiprows=2)
            df.dropna(axis=1, how="all", inplace=True)
            return df
        except Exception as e:
            self.handle_error(e)
            return pd.DataFrame()

    def panel(self):
        if self.format == "Plate Format":
            self.switch_plate_format_visibility(True)
            self.switch_wide_format_visibility(False)
        else:
            self.switch_plate_format_visibility(False)
            self.switch_wide_format_visibility(True)
        return self._view

    @param.output(
        ("data", param.Dynamic),
        ("saliva_type", param.String),
        ("sample_times", param.List),
    )
    def output(self):
        if self.format == "Plate Format":
            self.process_plate_format()
        elif self.format == "Wide Format":
            self.process_wide_format()
        else:
            self.handle_error(ValueError("No format selected"))
        return (
            self.data,
            self.saliva_type,
            self.sample_times_input.value,
        )

    def process_plate_format(self):
        try:
            self.data = load_saliva_plate(
                self.temporary_dataframe,
                self.saliva_type,
                (
                    self.select_sample_id_col.value
                    if self.select_sample_id_col.value != ""
                    else None
                ),
                (
                    self.select_data_col.value
                    if self.select_data_col.value != ""
                    else None
                ),
                (
                    self.select_id_col_names.value
                    if len(self.select_id_col_names.value) > 0
                    else None
                ),
                (self.regex_input.value if self.regex_input.value != "" else None),
                condition_list=(
                    self.condition_list if self.condition_list is not None else None
                ),
            )
        except Exception as e:
            self.handle_error(e)
            self.ready = False

    def process_wide_format(self):
        try:
            self.data = load_saliva_wide_format(
                self.temporary_dataframe,
                self.saliva_selector.value,
                self.select_subject_col.value,
                self.select_condition_col.value,
                self.select_additional_index_cols.value,
                self.sample_times_input.value,
            )
            self.ready = True
        except Exception as e:
            self.handle_error(e)
            self.ready = False
