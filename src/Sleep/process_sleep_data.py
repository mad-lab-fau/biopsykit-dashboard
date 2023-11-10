import panel as pn
import param
import biopsykit as bp

from src.Sleep.sleep_base import SleepBase
import traceback


class ProcessDataParameters(SleepBase):

    # TODO -> wann acceleration, wann actigraph?
    def show_parameters(self) -> pn.Column:
        col = pn.Column()
        for pipeline_type in self.possible_processing_parameters.keys():
            params = self.possible_processing_parameters[pipeline_type]
            col.append(pn.pane.Markdown(f"## {pipeline_type}"))
            for parameter, options in params.items():
                if options is None:
                    continue
                if isinstance(options, list):
                    if parameter == "algorithm_type":
                        widget = pn.widgets.Select(
                            name=parameter,
                            options=options,
                        )
                        widget.link(
                            (pipeline_type, widget.name),
                            callbacks={"value": self.parameter_changed},
                        )
                        # widget.param.watch(self.parameter_changed, "value")
                        col.append(widget)
                    else:
                        widget = pn.widgets.MultiChoice(
                            name=parameter,
                            options=options,
                        )
                        widget.link(
                            (pipeline_type, widget.name),
                            callbacks={"value": self.parameter_changed},
                        )
                        col.append(widget)
                elif isinstance(options, bool):
                    widget = pn.widgets.Checkbox(
                        name=parameter,
                        value=options,
                    )
                    widget.link(
                        (pipeline_type, widget.name),
                        callbacks={"value": self.parameter_changed},
                    )
                    col.append(widget)
                elif isinstance(options, int):
                    widget = pn.widgets.IntInput(
                        name=parameter,
                        value=options,
                    )
                    widget.link(
                        (pipeline_type, widget.name),
                        callbacks={"value": self.parameter_changed},
                    )
                    col.append(widget)
                elif isinstance(options, float):
                    widget = pn.widgets.FloatInput(
                        name=parameter,
                        value=options,
                    )
                    widget.link(
                        (pipeline_type, widget.name),
                        callbacks={"value": self.parameter_changed},
                    )
                    col.append(widget)
            col.append(pn.layout.Divider())
        return col

    def parameter_changed(self, event):
        self.processing_parameters[event.obj.name] = event.new

    # TODO brauchen noch sampling_rate und zuordnung zwischen data
    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
        ("processing_parameters", param.Dict),
        ("processed_data", param.Dynamic),
        ("possible_processing_parameters", param.Dict),
    )
    def output(self):
        self.processed_data = {}
        for key in self.data.keys():
            self.processed_data[key] = {"acceleration": {}, "actigraph": {}}
            pn.state.notifications.info(f"Processing {key}...")
            try:
                self.processed_data[key][
                    "acceleration"
                ] = bp.sleep.sleep_processing_pipeline.predict_pipeline_acceleration(
                    data=self.data[key],
                    sampling_rate=self.sampling_rate,
                    epoch_length=60
                    # **self.processing_parameters["acceleration"],
                )
            except Exception as e:
                traceback.print_exc()
                pn.state.notifications.error(
                    f"Error while processing {key} with pipeline: acceleration led to Error:{e}"
                )
            try:
                self.processed_data[key][
                    "actigraph"
                ] = bp.sleep.sleep_processing_pipeline.predict_pipeline_actigraph(
                    data=self.data[key],
                    **self.processing_parameters["actigraph"],
                )
            except Exception as e:
                pn.state.notifications.error(
                    f"Error while processing {key} with pipeline: actigraph led to Error {e}"
                )
        pn.state.notifications.success("Processing finished!")
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
            self.processing_parameters,
            self.processed_data,
            self.possible_processing_parameters,
        )

    def panel(self):
        text = "# Processing Parameters \n Below you can choose the processing parameters for your data. If you are unsure, just leave the default values."
        return pn.Column(pn.pane.Markdown(text), self.show_parameters())
