import numpy as np
import panel as pn
import param
import biopsykit as bp
from biopsykit.utils.datatype_helper import SalivaMeanSeDataFrame


class ShowSalivaFeatures(param.Parameterized):
    data = param.Dynamic(default=None)
    saliva_type = param.String(default=None)
    sample_times = param.Dynamic(default=[-30, -1, 30, 40, 50, 60, 70])
    auc_args = {"remove_s0": False, "compute_auc_post": False, "sample_times": None}
    slope_args = {"sample_idx": None, "sample_labels": None}
    standard_features_args = {"group_cols": None, "keep_index": True}
    mean_se_args = {
        "test_times": None,
        "sample_times_absolute": False,
        "test_title": "Test",
        "remove_s0": False,
    }

    def feature_accordion(self) -> pn.Accordion:
        if self.data is None:
            return pn.Accordion()
        if self.saliva_type is None:
            return pn.Accordion()
        acc = pn.Accordion()
        acc.append(self.get_mean_se_element())
        acc.append(self.get_auc())
        acc.append(self.get_max_increase())
        # acc.append(self.get_slope())
        acc.append(self.get_max_value())
        acc.append(self.get_standard_features())
        acc.append(self.get_initial_value())
        return acc

    def get_mean_se_element(self):
        col = pn.Column(name="Mean and SE")
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

        col.append(tab)
        col.append(
            pn.Row(
                filename,
                button,
            )
        )
        col.append(pn.layout.Divider())
        col.append(self.edit_mean_se_figure())
        return col

    def get_mean_se_df(self) -> SalivaMeanSeDataFrame:
        return bp.saliva.mean_se(
            data=self.data,
            saliva_type=self.saliva_type,
        )

    def edit_mean_se_figure(self):
        remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        sample_times_absolut = pn.widgets.Checkbox(
            name="Sample Times Absolute", value=False
        )
        # [0, 30]
        test_times = pn.widgets.ArrayInput(name="Test Times", value=np.array([]))
        title = pn.widgets.TextInput(name="Title", value="TEST")
        plot = pn.pane.Matplotlib(
            self.get_mean_se_figure(), format="svg", sizing_mode="scale_both"
        )
        remove_s0.link(plot, callbacks={"value": self.update_mean_se_figure})
        sample_times_absolut.link(plot, callbacks={"value": self.update_mean_se_figure})
        test_times.link(plot, callbacks={"value": self.update_mean_se_figure})
        title.link(plot, callbacks={"value": self.update_mean_se_figure})
        return pn.Row(
            pn.Column(remove_s0, sample_times_absolut, test_times, title),
            plot,
        )

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

    def get_mean_se_figure(self) -> pn.pane.Matplotlib:
        fig, _ = bp.protocols.plotting.saliva_plot(
            self.get_mean_se_df(),
            saliva_type=self.saliva_type,
            sample_times=self.sample_times,
            **self.mean_se_args,
        )
        return fig

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
            data=self.data,
            saliva_type=self.saliva_type,
            **self.auc_args,
        )
        target.value = auc_df

    def get_auc(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Checkbox(
            name="Remove S0", value=False, align=("start", "start")
        )
        compute_auc_post = pn.widgets.Checkbox(name="Compute AUC Post", value=False)
        auc_df = bp.saliva.auc(
            data=self.data,
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

    def max_value_switch_removes0(self, target, event):
        target.value = bp.saliva.max_value(self.data, remove_s0=event.new)

    def get_max_value(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        df = bp.saliva.max_value(self.data, remove_s0=switch_remove_s0.value)
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
        df = bp.saliva.standard_features(
            data=self.data,
            saliva_type=self.saliva_type,
            **self.standard_features_args,
        )
        target.value = df

    def get_standard_features(self) -> pn.Column:
        group_cols = pn.widgets.MultiChoice(
            name="Group Columns", value=[], options=list(self.data.columns)
        )
        keep_index = pn.widgets.Checkbox(name="Keep Index", value=True)
        df = bp.saliva.standard_features(
            self.data,
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
            text_kwargs={"name": "Enter filename", "value": "standard_features.csv"},
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

    def initial_value_switch_removes0(self, target, event):
        target.value = bp.saliva.initial_value(self.data, remove_s0=event.new)

    def get_initial_value(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        df = bp.saliva.initial_value(self.data, remove_s0=switch_remove_s0.value)
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

    def max_increase_switch_removes0(self, target, event):
        target.value = bp.saliva.max_increase(self.data, remove_s0=event.new)

    def get_max_increase(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Checkbox(name="Remove S0", value=False)
        df = bp.saliva.max_increase(self.data)
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
            self.data,
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

    def panel(self):
        co = pn.Column()
        co.append(pn.pane.Markdown("# Show Features"))
        acc = self.feature_accordion()
        co.append(acc)
        return co
