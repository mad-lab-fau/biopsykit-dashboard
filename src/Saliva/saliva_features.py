import panel as pn
import param
import biopsykit as bp


class ShowSalivaFeatures(param.Parameterized):
    data = param.Dynamic(default=None)
    saliva_type = param.String(default=None)
    sample_times = param.Dynamic(default=None)

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

    def get_auc(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
        compute_auc_post = pn.widgets.Switch(name="Compute AUC Post", value=False)
        sample_times_input = pn.widgets.ArrayInput(
            name="Sample Times",
            value=self.sample_times,
            placeholder="Enter the sample times in Array form, e.g. [-30, -1, 30, 40]",
        )
        auc_df = bp.saliva.auc(
            data=self.data,
            saliva_type=self.saliva_type,
            sample_times=(
                sample_times_input.value if sample_times_input.value != [] else None
            ),
            remove_s0=switch_remove_s0.value,
            compute_auc_post=compute_auc_post.value,
        )
        col = pn.Column(name="AUC")
        col.append(switch_remove_s0)
        col.append(sample_times_input)
        col.append(
            pn.widgets.Tabulator(
                auc_df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

    def get_max_value(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
        df = bp.saliva.max_value(self.data, remove_s0=switch_remove_s0.value)
        col = pn.Column(name="Max Value")
        col.append(switch_remove_s0)
        col.append(
            pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

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
        col = pn.Column(name="Standard Features")
        col.append(group_cols)
        col.append(keep_index)
        col.append(
            pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

    def get_initial_value(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
        df = bp.saliva.initial_value(self.data, remove_s0=switch_remove_s0.value)
        col = pn.Column(name="Initial Value")
        col.append(switch_remove_s0)
        col.append(
            pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
        return col

    def get_max_increase(self) -> pn.Column:
        switch_remove_s0 = pn.widgets.Switch(name="Remove S0", value=False)
        df = bp.saliva.max_increase(self.data)
        col = pn.Column(name="Max Increase")
        col.append(switch_remove_s0)
        col.append(
            pn.widgets.Tabulator(
                df, pagination="local", layout="fit_data_stretch", page_size=10
            )
        )
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
