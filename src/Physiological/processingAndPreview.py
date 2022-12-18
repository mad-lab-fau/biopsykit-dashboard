import param
import panel as pn


class ProcessingAndPreview(param.Parameterized):
    ecg_processor = param.Dynamic()
    textHeader = ''

    def panel(self):
        if self.textHeader == "":
            f = open('../assets/Markdown/ProcessingAndPreview.md', 'r')
            fileString = f.read()
            self.textHeader = fileString
        if self.ecg_processor is None:
            return pn.Column(
                pn.widgets.StaticText(name='Error:', value=' Processing went wrong')
            )
        column = pn.Column(
            self.textHeader
        )
        accordion = self.get_dataframes_as_accordions()
        for stat_value in self.get_statistical_values():
            accordion.append(stat_value)
        column.append(accordion)
        return column

    def get_dataframes_as_accordions(self):
        ecg_results = pn.widgets.DataFrame(value= self.ecg_processor.ecg_result['Data'])
        hr_results = pn.widgets.DataFrame(value=self.ecg_processor.hr_result['Data'])
        return pn.Accordion(('ECG Results', ecg_results), ('HR Results', hr_results))

    def get_statistical_values(self):
        ecg_stats = self.ecg_processor.ecg_result['Data'].agg({
            'ECG_Raw': ["min", "max", 'min', "median"],
            'ECG_Clean': ["min", "max", 'min', "median"],
            'ECG_Quality': ["min", "max", 'min', "median"],
            'Heart_Rate': ["min", "max", 'min', "median"],
            }
        )
        heart_rate_stats = self.ecg_processor.heart_rate['Data'].agg({
            'Heart_Rate': ["min", "max", 'min', "median"],
            }
        )
        return [('ECG Statistical Values', pn.widgets.DataFrame(value=ecg_stats)),
                ('Heart Rate Statistical Values', pn.widgets.DataFrame(value=heart_rate_stats))]

    @param.output(('ecg_processor', param.Dynamic))
    def output(self):
        return self.ecg_processor
