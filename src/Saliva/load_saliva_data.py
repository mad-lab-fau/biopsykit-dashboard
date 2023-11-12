import pandas as pd
import panel as pn
import param

from src.Saliva.SALIVA_CONSTANTS import LOAD_PLATE_DATA_TEXT
from src.Saliva.SalivaBase import SalivaBase
from src.utils import load_saliva_plate, load_saliva_wide_format


class LoadSalivaData(SalivaBase):
    ready = param.Boolean(default=False)
    temporary_dataframe = param.DataFrame(default=None)
    upload_btn = pn.widgets.FileInput(
        accept=".csv,.xls,.xlsx", multiple=False, sizing_mode="stretch_width"
    )
    select_saliva = pn.widgets.Select(
        name="Choose the saliva type",
        options=["", "cortisol", "amylase"],
        visible=False,
        sizing_mode="stretch_width",
    )
    select_subject_col = pn.widgets.Select(
        name="Select Subject Column",
        options=[],
        visible=False,
        sizing_mode="stretch_width",
    )
    select_condition_col = pn.widgets.Select(
        name="Select Condition Column",
        options=[],
        visible=False,
        sizing_mode="stretch_width",
    )
    select_additional_index_cols = pn.widgets.MultiChoice(
        name="Select Additional Index Columns",
        options=[],
        visible=False,
        sizing_mode="stretch_width",
    )
    sample_times_input = pn.widgets.TextInput(
        name="Sample Times",
        placeholder="Enter sample times separated by commas, e.g. [-30,10,30,60]",
        visible=False,
        sizing_mode="stretch_width",
    )
    select_id_col_names = pn.widgets.MultiChoice(
        name="Select Id Columns", options=[], visible=False, sizing_mode="stretch_width"
    )
    select_sample_id_col = pn.widgets.Select(
        name="Select Sample ID Column",
        options=[],
        visible=False,
        sizing_mode="stretch_width",
    )
    select_data_col = pn.widgets.Select(
        name="Select Data Column",
        options=[],
        visible=False,
        sizing_mode="stretch_width",
    )
    regex_input = pn.widgets.TextInput(
        name="Regex for sample id",
        value=None,
        placeholder="regular expression to extract subject ID, day ID and sample ID from the sample identifier",
        visible=False,
        sizing_mode="stretch_width",
    )
    fill_condition_list = pn.widgets.Checkbox(
        name="Set Condition List", visible=False, sizing_mode="stretch_width"
    )

    def __init__(self, **params):
        params["HEADER_TEXT"] = LOAD_PLATE_DATA_TEXT
        super().__init__(**params)
        self.update_step(3)
        self.update_text(LOAD_PLATE_DATA_TEXT)
        self.filename = None
        self.select_saliva.link(self, callbacks={"value": self.saliva_type_changed})
        self.upload_btn.link(self, callbacks={"filename": self.filename_changed})
        self._view = pn.Column(
            self.header,
            self.upload_btn,
            self.select_saliva,
            self.get_wide_format_column(),
            self.get_plate_format_column(),
        )

    def filename_changed(self, _, event):
        self.filename = event.new
        if (
            self.filename is None
            or self.filename == ""
            or "." not in self.filename
            or self.upload_btn.value is None
        ):
            return
        self.parse_file_input()

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
        self.ready = self.is_ready()

    def parse_file_input(self):
        if ".csv" in self.filename:
            self.temporary_dataframe = self.handle_csv_file(self.upload_btn.value)
        elif ".xls" in self.filename:
            self.temporary_dataframe = self.handle_excel_file(self.upload_btn.value)
        if self.temporary_dataframe.empty:
            self.handle_error(ValueError("No data loaded"))
            return
        try:
            self.temporary_dataframe.dropna(axis=1, how="all", inplace=True)
            self.fill_options()
            self.show_param_input(True)
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            self.show_param_input(False)
            self.handle_error(e)

    def fill_options(self):
        if self.format == "Plate Format":
            self.select_sample_id_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_data_col.options = [""] + list(self.temporary_dataframe.columns)
            self.select_id_col_names.options = list(self.temporary_dataframe.columns)
        elif self.format == "Wide Format":
            self.select_subject_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_condition_col.options = [""] + list(
                self.temporary_dataframe.columns
            )
            self.select_additional_index_cols.options = list(
                self.temporary_dataframe.columns
            )

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

    def show_param_input(self, visibility: bool):
        self.select_saliva.visible = visibility
        if not visibility:
            self.switch_plate_format_visibility(False)
            self.switch_wide_format_visibility(False)
            return
        if self.format == "Plate Format":
            self.switch_plate_format_visibility(True)
            self.switch_wide_format_visibility(False)
        else:
            self.switch_plate_format_visibility(False)
            self.switch_wide_format_visibility(True)

    def panel(self):
        show_param_input = self.data is not None and len(self.data) > 0
        self.show_param_input(show_param_input)
        return self._view

    @param.output(
        ("condition_list", param.Dynamic),
        ("format", param.String),
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
            self.condition_list,
            self.format,
            self.data,
            self.saliva_type,
            self.sample_times_input.value,
        )

    def process_plate_format(self):
        try:
            self.data = load_saliva_plate(
                file=self.temporary_dataframe,
                saliva_type=self.select_saliva.value,
                sample_id_col=(
                    self.select_sample_id_col.value
                    if self.select_sample_id_col.value != ""
                    else None
                ),
                data_col=(
                    self.select_data_col.value
                    if self.select_data_col.value != ""
                    else None
                ),
                id_col_names=(
                    self.select_id_col_names.value
                    if len(self.select_id_col_names.value) > 0
                    else None
                ),
                regex=(
                    self.regex_input.value if self.regex_input.value != "" else None
                ),
                condition_list=(
                    self.condition_list
                    if self.condition_list is not None
                    and self.fill_condition_list.value
                    else None
                ),
            )
        except Exception as e:
            self.handle_error(e)

    def is_ready(self) -> bool:
        if self.saliva_type == "":
            return False
        return True

    def process_wide_format(self):
        try:
            self.data = load_saliva_wide_format(
                self.temporary_dataframe,
                self.select_saliva.value,
                self.select_subject_col.value,
                self.select_condition_col.value,
                self.select_additional_index_cols.value,
                self.sample_times_input.value,
            )
            self.ready = self.is_ready()
        except Exception as e:
            self.handle_error(e)
