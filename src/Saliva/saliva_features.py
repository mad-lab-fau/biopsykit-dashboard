import io
import itertools
from typing import Tuple, Dict

import matplotlib.figure
import numpy as np
import pandas as pd
import panel as pn
import param
import biopsykit as bp
from biopsykit.utils.datatype_helper import SalivaMeanSeDataFrame
from fau_colors import cmaps
from numpy import ndarray

from src.Saliva.SALIVA_CONSTANTS import SHOW_FEATURES_TEXT
from src.Saliva.SalivaBase import SalivaBase


class ShowSalivaFeatures(SalivaBase):
    data_features = param.Dynamic(default=None)
    auc_args = {"remove_s0": False, "compute_auc_post": False}
    slope_args = {"sample_idx": None, "sample_labels": None}
    standard_features_args = {"group_cols": None, "keep_index": True}
    mean_se_args = {
        "test_times": [],
        "sample_times_absolute": False,
        "test_title": "Test",
        "remove_s0": False,
    }
    feature_boxplot_args = {
        "x": None,
        "hue": None,
        "feature": None,
        "palette": cmaps.faculties_light,
    }
    multi_feature_boxplot_args = {
        "hue": None,
        "hue_order": None,
        "features": None,
        "palette": cmaps.faculties_light,
    }
    feature_accordion_column = pn.Column(pn.Accordion(name="Features"))
    exclude_subjects = pn.widgets.MultiChoice(
        name="Exclude Subjects", options=[], sizing_mode="stretch_width"
    )

    def get_feature_accordion(self) -> pn.Accordion:
        if self.saliva_type is None:
            return pn.Accordion()
        if self.get_data()[self.saliva_type] is None:
            return pn.Accordion()
        acc = pn.Accordion(name="Features", sizing_mode="stretch_width")
        acc.append(self.get_mean_se_element())
        acc.append(self.get_auc())
        acc.append(self.get_max_increase())
        acc.append(self.get_max_value())
        acc.append(self.get_standard_features())
        acc.append(self.get_initial_value())
        # acc.append(self.get_feature_boxplot_element())
        # acc.append(self.get_multi_feature_boxplot_element())
        return acc

    def get_mean_se_element(self):
        try:
            tab = pn.widgets.Tabulator(
                value=self.get_mean_se_df(),
                name="Mean and SE",
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
            )
            filename, button = tab.download_menu(
                text_kwargs={"name": "Enter filename", "value": "mean_se.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="Mean and SE")
            col.append(tab)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            # col.append(pn.layout.Divider())
            # col.append(self.edit_mean_se_figure())
            # download_btn = pn.widgets.FileDownload(
            #     label="Download",
            #     button_type="primary",
            #     callback=pn.bind(self.download_mean_se_figure),
            #     filename="figure.png",
            # )
            # col.append(download_btn)
            return col
        except Exception as e:
            pn.state.notifications.error("Error in Mean and SE")
            print("crashed in mean and se")
            col = pn.Column(name="Mean and SE")
            col.append(pn.pane.Str(str(e)))
            return col

    def get_mean_se_df(self) -> SalivaMeanSeDataFrame:
        return bp.saliva.mean_se(
            data=self.get_data()[self.saliva_type],
            saliva_type=self.saliva_type,
        )

    def edit_mean_se_figure(self):
        remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        sample_times_absolut = pn.widgets.Checkbox(
            name="Sample Times Absolute", value=False
        )
        test_times = pn.widgets.ArrayInput(name="Test Times", value=np.array([]))
        title = pn.widgets.TextInput(name="Title", value="Mean_SE_Figure")
        plot = pn.pane.Matplotlib(
            object=self.get_mean_se_figure(),
            format="svg",
            tight=True,
        )
        remove_s0.link(plot, callbacks={"value": self.update_mean_se_figure})
        sample_times_absolut.link(plot, callbacks={"value": self.update_mean_se_figure})
        test_times.link(plot, callbacks={"value": self.update_mean_se_figure})
        title.link(plot, callbacks={"value": self.update_mean_se_figure})
        return pn.Column(remove_s0, sample_times_absolut, test_times, title, plot)

    def update_mean_se_figure(self, target, event):
        if event.cls.name == "Title":
            self.mean_se_args["test_title"] = event.new
        elif event.cls.name == "Test Times":
            self.mean_se_args["test_times"] = list(event.new)
        elif event.cls.name == "Sample Times Absolute":
            self.mean_se_args["sample_times_absolute"] = event.new
        elif event.cls.name == "Remove S0":
            self.mean_se_args["remove_s0"] = event.new
        target.object = self.get_mean_se_figure()

    def get_mean_se_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, ax = bp.protocols.plotting.saliva_plot(
                self.get_mean_se_df(),
                saliva_type=self.saliva_type,
                sample_times=self.sample_times,
                **self.mean_se_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure(figsize=(10, 10))

    def download_mean_se_figure(self):
        buf = io.BytesIO()
        fig = self.get_mean_se_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def get_feature_boxplot_element(self) -> pn.Column:
        try:
            plot = pn.pane.Matplotlib(self.get_feature_boxplot_figure(), format="svg")
            col = pn.Column(name="Feature Boxplot")
            x_select = pn.widgets.Select(
                name="x",
                value=None,
                options=list(x.name for x in self.data_features.index.levels),
            )
            hue_textInput = pn.widgets.TextInput(name="hue", value="condition")
            feature_multichoice = pn.widgets.MultiChoice(
                name="feature", value=[], options=[]
            )
            hue_textInput.link(
                plot, callbacks={"value": self.update_feature_boxplot_figure}
            )
            x_select.link(plot, callbacks={"value": self.update_feature_boxplot_figure})
            feature_multichoice.link(
                plot, callbacks={"value": self.update_feature_boxplot_figure}
            )
            download_btn = pn.widgets.FileDownload(
                label="Download",
                button_type="primary",
                callback=pn.bind(self.download_boxplot_figure),
                filename="mean_se_figure.png",
            )
            col.append(
                pn.Row(
                    pn.Column(hue_textInput, x_select, feature_multichoice),
                    plot,
                )
            )
            col.append(pn.layout.Divider())
            col.append(download_btn)
            return col
        except Exception as e:
            col = pn.Column(name="Feature Boxplot")
            col.append(pn.pane.Str(str(e)))
            return col

    def download_boxplot_figure(self):
        buf = io.BytesIO()
        fig = self.get_feature_boxplot_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def update_feature_boxplot_figure(self, target, event):
        if event.cls.name == "x":
            self.feature_boxplot_args["x"] = event.new
        elif event.cls.name == "hue":
            self.feature_boxplot_args["hue"] = event.new
        elif event.cls.name == "feature":
            self.feature_boxplot_args["feature"] = event.new
        target.object = self.get_feature_boxplot_figure()

    def get_feature_boxplot_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, _ = bp.protocols.plotting.saliva_feature_boxplot(
                data=self.data_features,
                saliva_type=self.saliva_type,
                **self.feature_boxplot_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure()

    def get_multi_feature_boxplot_element(self) -> pn.Column:
        try:
            plot = pn.pane.Matplotlib(
                self.get_multi_feature_boxplot_figure(),
                format="svg",
            )
            col = pn.Column(name="Multi Feature Boxplot")
            hue_multiChoice = pn.widgets.MultiChoice(
                name="hue",
                value=[],
                options=list(x.name for x in self.data_features.index.levels),
                max_items=1,
            )
            hue_order_multichoice = pn.widgets.MultiChoice(
                name="hue_order",
                value=[],
                max_items=1,
                options=list(x.values for x in self.data_features.index.levels),
            )
            features_multichoice = pn.widgets.MultiChoice(
                name="features",
                value=[],
                options=list(
                    itertools.chain(
                        *list(x.values for x in self.data_features.index.levels)
                    )
                ),
            )
            hue_multiChoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            hue_order_multichoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            features_multichoice.link(
                plot, callbacks={"value": self.update_multi_feature_boxplot_figure}
            )
            download_btn = pn.widgets.FileDownload(
                label="Download",
                button_type="primary",
                callback=pn.bind(self.download_multi_boxplot_figure),
                filename="figure.png",
            )
            col.append(
                pn.Row(
                    pn.Column(
                        hue_multiChoice, hue_order_multichoice, features_multichoice
                    ),
                    plot,
                )
            )
            col.append(pn.layout.Divider())
            col.append(download_btn)
            return col
        except Exception as e:
            col = pn.Column(name="Multi Feature Boxplot")
            col.append(pn.pane.Str(str(e)))
            return col

    def download_multi_boxplot_figure(self):
        buf = io.BytesIO()
        fig = self.get_multi_feature_boxplot_figure()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def update_multi_feature_boxplot_figure(self, target, event):
        if event.cls.name == "features":
            new_value = event.new if len(event.new) > 0 else None
        else:
            new_value = event.new[0] if len(event.new) > 0 else None
        if isinstance(new_value, ndarray):
            new_value = new_value.tolist()
        self.multi_feature_boxplot_args[event.cls.name] = new_value
        target.object = self.get_multi_feature_boxplot_figure()

    def get_multi_feature_boxplot_figure(self) -> matplotlib.figure.Figure:
        try:
            fig, _ = bp.protocols.plotting.saliva_multi_feature_boxplot(
                data=self.data_features,
                saliva_type=self.saliva_type,
                **self.multi_feature_boxplot_args,
            )
            return fig
        except Exception:
            return matplotlib.figure.Figure()

    def filter_auc(self, target, event):
        if event is None or event.cls is None:
            return
        if event.cls.name == "Remove S0":
            self.auc_args["remove_s0"] = event.new
        elif event.cls.name == "Compute AUC Post":
            self.auc_args["compute_auc_post"] = event.new
        elif event.cls.name == "Sample Times":
            self.auc_args["sample_times"] = event.new
        else:
            return
        auc_df = bp.saliva.auc(
            data=self.get_data()[self.saliva_type],
            saliva_type=self.saliva_type,
            **self.auc_args,
        )
        target.value = auc_df

    def get_auc(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(
                name="Remove S0", value=False, align=("start", "start")
            )
            compute_auc_post = pn.widgets.Checkbox(name="Compute AUC Post", value=False)
            auc_df = bp.saliva.auc(
                data=self.get_data()[self.saliva_type],
                saliva_type=self.saliva_type,
                sample_times=self.sample_times,
                remove_s0=switch_remove_s0.value,
                compute_auc_post=compute_auc_post.value,
            )
            auc_tabulator = pn.widgets.Tabulator(
                auc_df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
                header_align="right",
            )
            switch_remove_s0.link(
                auc_tabulator,
                callbacks={"value": self.filter_auc},
            )
            compute_auc_post.link(auc_tabulator, callbacks={"value": self.filter_auc})
            filename, button = auc_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "auc.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="AUC")
            col.append(
                pn.Row(
                    "**Remove s0**",
                    switch_remove_s0,
                    pn.layout.HSpacer(),
                    align=("center"),
                )
            )
            col.append(pn.Row("**Compute AUC Post**", compute_auc_post))
            col.append(auc_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="AUC")
            col.append(pn.pane.Str(str(e)))
            return col

    def max_value_switch_removes0(self, target, event):
        target.value = bp.saliva.max_value(
            self.get_data()[self.saliva_type], remove_s0=event.new
        )

    def get_max_value(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.max_value(
                self.get_data()[self.saliva_type], remove_s0=switch_remove_s0.value
            )
            max_value_tabulator = pn.widgets.Tabulator(
                df,
                pagination="local",
                layout="fit_data_stretch",
                page_size=10,
                header_align="right",
            )
            filename, button = max_value_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "max_value.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            switch_remove_s0.link(
                max_value_tabulator, callbacks={"value": self.max_value_switch_removes0}
            )
            col = pn.Column(name="Max Value")
            col.append(pn.Row("**Remove s0**", switch_remove_s0, pn.layout.HSpacer()))
            col.append(max_value_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Max Value")
            col.append(pn.pane.Str(str(e)))
            return col

    def change_standard_feature(self, target, event):
        if event is None or event.cls is None:
            return
        if event.cls.name == "Group Columns":
            self.standard_features_args["group_cols"] = (
                event.new if event.new != [] else None
            )
        elif event.cls.name == "Keep Index":
            self.standard_features_args["keep_index"] = event.new
        else:
            return
        # try:
        df = bp.saliva.standard_features(
            data=self.get_data()[self.saliva_type],
            saliva_type=self.saliva_type,
            **self.standard_features_args,
        )
        target.value = df
        # except Exception as e:
        #     pn.state.notifications.error(e)
        #     target.value = pd.DataFrame()

    def get_standard_features(self) -> pn.Column:
        try:
            group_cols = pn.widgets.MultiChoice(
                name="Group Columns",
                value=[],
                options=list(self.get_data()[self.saliva_type].columns),
            )
            keep_index = pn.widgets.Checkbox(name="Keep Index", value=True)
            df = bp.saliva.standard_features(
                self.get_data()[self.saliva_type],
                saliva_type=self.saliva_type,
                group_cols=(group_cols.value if group_cols.value != [] else None),
                keep_index=keep_index.value,
            )
            standard_features_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            group_cols.link(
                standard_features_tabulator,
                callbacks={"value": self.change_standard_feature},
            )
            keep_index.link(
                standard_features_tabulator,
                callbacks={"value": self.change_standard_feature},
            )
            filename, button = standard_features_tabulator.download_menu(
                text_kwargs={
                    "name": "Enter filename",
                    "value": "standard_features.csv",
                },
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="Standard Features")
            col.append(group_cols)
            col.append(keep_index)
            col.append(standard_features_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Standard Features")
            col.append(pn.pane.Str(str(e)))
            return col

    def initial_value_switch_removes0(self, target, event):
        target.value = bp.saliva.initial_value(
            self.get_data()[self.saliva_type], remove_s0=event.new
        )

    def get_initial_value(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.initial_value(
                self.get_data()[self.saliva_type], remove_s0=switch_remove_s0.value
            )
            initial_value_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            filename, button = initial_value_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "initial_value.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            switch_remove_s0.link(
                initial_value_tabulator,
                callbacks={"value": self.initial_value_switch_removes0},
            )
            col = pn.Column(name="Initial Value")
            col.append(pn.Row("**Remove s0**", switch_remove_s0))
            col.append(initial_value_tabulator)
            col.append(
                pn.Row(
                    filename,
                    button,
                )
            )
            return col
        except Exception as e:
            col = pn.Column(name="Initial Value")
            col.append(pn.pane.Str(str(e)))
            return col

    def max_increase_switch_removes0(self, target, event):
        target.value = bp.saliva.max_increase(
            self.get_data()[self.saliva_type], remove_s0=event.new
        )

    def get_max_increase(self) -> pn.Column:
        try:
            switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
            df = bp.saliva.max_increase(self.get_data()[self.saliva_type])
            max_increase_tabulator = pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
            switch_remove_s0.link(
                max_increase_tabulator,
                callbacks={"value": self.max_increase_switch_removes0},
            )
            filename, button = max_increase_tabulator.download_menu(
                text_kwargs={"name": "Enter filename", "value": "max_increase.csv"},
                button_kwargs={
                    "name": "Download table",
                    "button_type": "primary",
                    "align": "end",
                },
            )
            col = pn.Column(name="Max Increase")
            col.append(pn.Row("**Remove s0**", switch_remove_s0))
            col.append(max_increase_tabulator)
            col.append(pn.Row(filename, button))
            return col
        except Exception as e:
            col = pn.Column(name="Max Increase")
            col.append(pn.pane.Str(str(e)))
            return col

    def get_slope(self) -> pn.Column:
        sample_times_input = pn.widgets.ArrayInput(
            name="Sample Times",
            value=self.sample_times,
            placeholder="Enter the sample times in Array form, e.g. [-30, -1, 30, 40]",
        )
        sample_idx = pn.widgets.ArrayInput(
            name="Sample Index", value=[1, 4], placeholder="Enter the sample index"
        )
        slope_df = bp.saliva.slope(
            self.get_data()[self.saliva_type],
            sample_idx=sample_idx.value,
            sample_times=sample_times_input.value,
            sample_labels=None,
        )
        col = pn.Column(name="Slope")
        col.append(sample_times_input)
        col.append(sample_idx)
        col.append(
            pn.widgets.Tabulator(
                slope_df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

    def get_data(self) -> Dict[str, pd.DataFrame]:
        return bp.utils.data_processing.exclude_subjects(
            excluded_subjects=self.exclude_subjects.value,
            condition_list=self.condition_list.tolist()
            if isinstance(self.condition_list, ndarray)
            else self.condition_list,
            **{self.saliva_type: self.data},
        )

    def update_feature_column(self, target, event):
        self.feature_accordion_column.__setitem__(0, self.get_feature_accordion())

    def get_all_subjects(self):
        try:
            return list(self.data.index.get_level_values("subject").unique())
        except Exception:
            return []

    def __init__(self, **params):
        params["HEADER_TEXT"] = SHOW_FEATURES_TEXT
        super().__init__(**params)
        self.update_step(4)
        self.update_text(SHOW_FEATURES_TEXT)
        self.exclude_subjects.link(
            self, callbacks={"value": self.update_feature_column}
        )
        self._view = pn.Column(
            self.header,
            self.exclude_subjects,
            pn.layout.Divider(),
            self.feature_accordion_column,
        )

    def panel(self):
        self.exclude_subjects.options = self.get_all_subjects()
        if self.exclude_subjects.options is None or self.exclude_subjects.options == []:
            self.exclude_subjects.visible = False
        if self.data_features is None and self.data is not None:
            try:
                self.data_features = bp.saliva.standard_features(
                    self.data, saliva_type=self.saliva_type
                )
            except Exception as e:
                print(f"Exception in computing features: {e}")
            try:
                self.data_features = bp.saliva.utils.saliva_feature_wide_to_long(
                    self.data_features, saliva_type=self.saliva_type
                )
            except Exception as e:
                print(f"Exception in converting to long format: {e}")
        self.update_feature_column(None, None)
        # self.feature_accordion_column.__setitem__(0, self.get_feature_accordion())
        return self._view
