import panel as pn
import param
import biopsykit as bp


class ShowSalivaFeatures(param.Parameterized):
    data = param.Dynamic(default=None)
    saliva_type = param.String(default=None)
    sample_times = param.Dynamic(default=[-30, -1, 30, 40, 50, 60, 70])
    auc_args = {"remove_s0": False, "compute_auc_post": False, "sample_times": None}
    slope_args = {"sample_idx": None, "sample_labels": None}
    standard_features_args = {"group_cols": None, "keep_index": True}

    def feature_accordion(self) -> pn.Accordion:
        if self.data is None:
            return pn.Accordion()
        if self.saliva_type is None:
            return pn.Accordion()
        acc = pn.Accordion()
        acc.append(self.get_mean_se())
        acc.append(self.get_auc())
        acc.append(self.get_max_increase())
        # acc.append(self.get_slope())
        acc.append(self.get_max_value())
        acc.append(self.get_standard_features())
        acc.append(self.get_initial_value())
        return acc

    def get_mean_se(self):
        df = bp.saliva.mean_se(
            data=self.data,
            saliva_type=self.saliva_type,
        )
        tab = pn.widgets.Tabulator(
            value=df,
            name="Mean and SE",
            pagination="local",
            layout="fit_data_stretch",
            page_size=10,
        )
        return tab

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
            sample_times=self.sample_times,
            remove_s0=self.auc_args["remove_s0"],
            compute_auc_post=self.auc_args["compute_auc_post"],
        )
        target.value = auc_df

    def get_auc(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Switch(
            name="Remove S0", value=False, align=("start", "start")
        )
        compute_auc_post = pn.widgets.Switch(name="Compute AUC Post", value=False)
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
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
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
            self.standard_features_args["group_cols"] = event.new
        elif event.cls.name == "Keep Index":
            self.standard_features_args["keep_index"] = event.new
        else:
            return
        df = bp.saliva.standard_features(
            data=self.data,
            saliva_type=self.saliva_type,
            group_cols=(
                self.standard_features_args["group_cols"]
                if self.standard_features_args["group_cols"] != []
                else None
            ),
            keep_index=self.standard_features_args["keep_index"],
        )
        target.value = df

    def get_standard_features(self) -> pn.Column:
        group_cols = pn.widgets.MultiChoice(
            name="Group Columns", value=[], options=list(self.data.columns)
        )
        keep_index = pn.widgets.Switch(name="Keep Index", value=True)
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
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
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
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
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
