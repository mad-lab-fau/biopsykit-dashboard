import panel as pn
import param
import biopsykit as bp


class ProcessDataParameters(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)
    processing_parameters = {}
    possible_processing_parameters = {
        "acceleration": {
            "convert_to_g": True,
            "algorithm_type": ["Cole/Kripke"],
            "epoch_length": 60,
        },
        "actigraph": {
            "algorithm_type": ["Cole/Kripke"],
            "bed_interval": [],
        },
    }

    # TODO -> wann acceleration, wann actigraph?
    def show_parameters(self) -> pn.Column:
        params = self.possible_processing_parameters["acceleration"]
        col = pn.Column()
        for parameter, options in params.items():
            if options is None:
                continue
            if isinstance(options, list):
                if parameter == "algorithm_type":
                    widget = pn.widgets.Select(
                        name=parameter,
                        options=options,
                    )
                    widget.param.watch(self.parameter_changed, "value")
                    col.append(widget)
                else:
                    widget = pn.widgets.MultiChoice(
                        name=parameter,
                        options=options,
                    )
                    widget.param.watch(self.parameter_changed, "value")
                    col.append(widget)
            elif isinstance(options, bool):
                widget = pn.widgets.Checkbox(
                    name=parameter,
                    value=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
            elif isinstance(options, int):
                widget = pn.widgets.IntInput(
                    name=parameter,
                    value=options,
                )
                widget.param.watch(self.parameter_changed, "value")
                col.append(widget)
        return col

    def parameter_changed(self, event):
        self.processing_parameters[event.obj.name] = event.new

    # TODO brauchen noch sampling_rate und zuordnung zwischen data
    @param.output(
        ("selected_device", param.String),
        ("data", param.Dynamic),
        ("processed_data", param.Dynamic),
    )
    def output(self):
        self.processed_data = []
        for ds in self.data:
            results = bp.sleep.sleep_processing_pipeline.predict_pipeline_actigraph(
                data=ds, **self.processing_parameters
            )
            self.processed_data.append(results)
        return (self.selected_device, self.data, self.processed_data)

    def panel(self):
        text = "# Processing Parameters \n Below you can choose the processing parameters for your data. If you are unsure, just leave the default values."
        return pn.Column(pn.pane.Markdown(text), self.show_parameters())
