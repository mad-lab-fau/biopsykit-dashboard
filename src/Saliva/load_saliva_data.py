from io import StringIO

import pandas as pd
import panel as pn
import param
import biopsykit as bp
from src.utils import load_saliva_plate, _load_dataframe, load_saliva_wide_format


class LoadSalivaDataPlate(param.Parameterized):
    data = param.Dynamic()
    format = param.String(default=None)
    upload_btn = pn.widgets.FileInput(accept=".csv,.xls,.xlsx", multiple=False)
    ready = param.Boolean(default=False)
    sample_id = param.String(default=None)
    data_col = param.Dynamic()
    id_col_names = param.Dynamic()
    regex_str = param.String(default=None)
    sample_times = param.Dynamic()
    condition_list = param.Dynamic()
    saliva_type = param.String(default="")
    df = param.DataFrame(default=None)
    plate_params_visible = False
    saliva_selector = pn.widgets.Select(
        name="Choose the saliva type",
        options=["", "Cortisol", "Amylase"],
        visible=False,
    )
    sample_id_col = pn.widgets.Select(
        name="Choose the sample id column", options=[], visible=False
    )
    data_col_selector = pn.widgets.Select(
        name="Choose the data column", options=[], visible=False
    )
    id_col_names_multi_choice = pn.widgets.MultiChoice(
        name="Choose the id columns",
        placeholder="Select the columns representing the IDs",
        options=[],
        visible=False,
    )
    regex_input = pn.widgets.TextInput(
        name="Regex for sample id",
        placeholder="regular expression to extract subject ID, day ID and sample ID from the sample identifier",
        visible=False,
    )

    def parse_file_input(self, target, event):
        try:
            self.df = pd.read_excel(self.upload_btn.value, skiprows=2)
            self.df.dropna(axis=1, how="all", inplace=True)
            self.show_param_input_plate()
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False
            self.hide_param_input()

    def show_param_input_plate(self):
        self.saliva_selector.visible = True
        self.sample_id_col.visible = True
        self.sample_id_col.options = [""] + list(self.df.columns)
        self.data_col_selector.visible = True
        self.data_col_selector.options = [""] + list(self.df.columns)
        self.id_col_names_multi_choice.visible = True
        self.id_col_names_multi_choice.options = list(self.df.columns)
        self.regex_input.visible = True

    def hide_param_input(self):
        self.saliva_selector.visible = False
        self.sample_id_col.visible = False
        self.data_col_selector.visible = False
        self.id_col_names_multi_choice.visible = False
        self.regex_input.visible = False

    def get_param_col(self) -> pn.Column:
        return pn.Column(
            self.saliva_selector,
            self.sample_id_col,
            self.data_col_selector,
            self.regex_input,
            self.id_col_names_multi_choice,
        )

    def saliva_type_changed(self, event):
        self.saliva_type = event.new
        if event.new == "":
            self.ready = False
        else:
            self.ready = True

    @param.output(
        ("data", param.Dynamic),
    )
    def output(self):
        self.data = load_saliva_plate(
            self.df,
            self.saliva_type,
            self.sample_id_col.value,
            self.data_col_selector.value,
            self.id_col_names_multi_choice.value,
            self.regex_input.value,
            self.condition_list,
        )
        return (self.data,)

    def panel(self):
        text = (
            "# Upload Saliva Data \n Here you can upload the saliva data. "
            "In the following steps you can analyze the data and then download the results."
        )
        self.saliva_selector.param.watch(self.saliva_type_changed, "value")
        self.upload_btn.link(None, callbacks={"value": self.parse_file_input})
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        col.append(self.upload_btn)
        col.append(self.get_param_col())
        return col


class LoadSalivaDataWide(param.Parameterized):
    data = param.Dynamic()
    format = param.String(default=None)
    saliva_selector = pn.widgets.Select(
        name="Choose the saliva type",
        options=["", "Cortisol", "Amylase"],
        visible=False,
    )
    upload_btn = pn.widgets.FileInput(accept=".csv,.xls,.xlsx", multiple=False)
    ready = param.Boolean(default=False)
    subject_col_selector = pn.widgets.Select(
        name="Choose the subject column", options=[], visible=False
    )
    condition_col_selector = pn.widgets.Select(
        name="Choose the condition column", options=[], visible=False
    )
    additional_cols_multi_choice = pn.widgets.MultiChoice(
        name="Choose the id columns",
        placeholder="Select the columns representing the IDs",
        options=[],
        visible=False,
    )

    def parse_file_input(self, target, event):
        try:
            self.df = pd.read_excel(self.upload_btn.value, skiprows=2)
            self.df.dropna(axis=1, how="all", inplace=True)
            self.show_param_input()
            pn.state.notifications.success("Files uploaded")
        except Exception as e:
            pn.state.notifications.error("Error while loading data: " + str(e))
            self.ready = False
            self.hide_param_input()

    def show_param_input(self):
        self.saliva_selector.visible = True
        self.subject_col_selector.visible = True
        self.subject_col_selector.options = [""] + list(self.df.columns)
        self.condition_col_selector.visible = True
        self.condition_col_selector.options = [""] + list(self.df.columns)
        self.additional_cols_multi_choice.visible = True
        self.additional_cols_multi_choice.options = [""] + list(self.df.columns)
        self.sample_times_input.visible = True

    def hide_param_input(self):
        self.saliva_selector.visible = False
        self.subject_col_selector.visible = False
        self.condition_col_selector.visible = False
        self.additional_cols_multi_choice.visible = False
        self.sample_times_input.visible = False

    def get_param_col(self) -> pn.Column:
        return pn.Column(
            self.subject_col_selector,
            self.condition_col_selector,
            self.additional_cols_multi_choice,
        )

    @param.output(
        ("data", param.Dynamic),
    )
    def output(self):
        self.data = load_saliva_wide_format(
            self.df,
            self.saliva_selector.value,
            self.subject_col_selector.value,
            self.condition_col_selector.value,
            self.additional_cols_multi_choice.value,
            self.sample_times_input.value,
        )
        return (self.data,)

    def panel(self):
        text = (
            "# Upload Saliva Data \n Here you can upload the saliva data. "
            "In the following steps you can analyze the data and then download the results."
        )
        self.upload_btn.link(None, callbacks={"value": self.parse_file_input})
        col = pn.Column()
        col.append(pn.pane.Markdown(text))
        col.append(self.upload_btn)
        col.append(self.get_param_col())
        return col
