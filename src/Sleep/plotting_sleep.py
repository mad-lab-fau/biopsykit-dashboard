import panel as pn
import param


class PlotResults(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)
