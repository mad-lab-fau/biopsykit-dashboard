import param
import panel as pn


class ProcessHRV(param.Parameterized):
    ecg_processor = param.Dynamic()
    textHeader = ''
    methods = ['hrv_time',
               'hrv_nonlinear',
               'hrv_frequency',
               'all']
    hrv_types = pn.widgets.MultiChoice(name='Methods', value=['hrv_time', 'hrv_nonlinear'], options=methods)
    correct_rpeaks = pn.widgets.Checkbox(name='Correct RPeaks', value=True)
    index = pn.widgets.TextInput(name='Index', value='')
    index_name = pn.widgets.TextInput(name='Index Name', value='')
    sampling_rate = pn.widgets.StaticText(name='Sampling Rate')
    process_btn = pn.widgets.Button(name='Process HRV')

    def panel(self):
        if self.textHeader == "":
            f = open('../assets/Markdown/ProcessHRV.md', 'r')
            fileString = f.read()
            self.textHeader = fileString
        self.sampling_rate.value = self.ecg_processor.sampling_rate
        self.process_btn.on_click(self.process_hrv)
        return pn.Column(
            pn.pane.Markdown(self.textHeader),
            self.hrv_types,
            self.correct_rpeaks,
            self.index,
            self.index_name,
            self.sampling_rate
        )

    def process_hrv(self):
        self.ecg_processor.hrv_process(self.ecg_processor, 'Data',
                                       index=self.index.value,
                                       index_name=self.index_name.value,
                                       hrv_types=self.hrv_types.value,
                                       correct_rpeaks=self.correct_rpeaks.value
                                       )
        pn.state.notifications.success('HRV processed successfully')
