import pandas as pd
import panel as pn
import param
import biopsykit as bp


class ResultsPreview(param.Parameterized):
    data = param.Dynamic(default=None)
    selected_device = param.String(default="")
    processed_data = param.Dynamic(default=None)

    def show_results(self) -> pn.Column:
        col = pn.Column()
        if len(self.processed_data) == 1:
            col.append(self.show_individual_results(self.processed_data[0]))
            return col
        result = 1
        accordion = pn.Accordion()
        for data in self.processed_data:
            results_col = self.show_individual_results(data)
            accordion.append((f"Result {result}", results_col))
            result += 1

    @staticmethod
    def show_individual_results(data) -> pn.Column:
        col = pn.Column()
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                col.append(pn.widgets.Tabulator(value, name=key))
                col.append(pn.layout.Divider())
            elif isinstance(value, list):
                text = pn.widgets.StaticText(name=key, value=value)
                col.append(text)
                col.append(pn.layout.Divider())
            elif isinstance(value, dict) and key == "sleep_endpoints":
                col.append(
                    pn.widgets.Tabulator(
                        bp.sleep.sleep_endpoints.endpoints_as_df(value), name=key
                    )
                )
                col.append(pn.layout.Divider())
            else:
                text = pn.widgets.StaticText(name=key, value=value)
                col.append(text)
                col.append(pn.layout.Divider())
        return col

    def panel(self):
        text = "# Results Preview \n Below you can see a preview of the results. If you are satisfied with the results, you can click 'Save Results' to save the results to your local machine."
        return pn.Column(pn.pane.Markdown(text), self.show_results())
