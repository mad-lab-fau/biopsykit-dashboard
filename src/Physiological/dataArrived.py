import param
import panel as pn
import pandas as pd
from nilspodlib import Session, SyncedSession
from src.utils import get_datetime_columns_of_data_frame, get_start_and_end_time


class DataArrived(param.Parameterized):
    synced = param.Boolean()
    session_type = param.String()
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    sampling_rate_input = pn.widgets.TextInput(name='Sampling rate Input',
                                               placeholder='Enter your sampling rate here...')
    text = ''
    info_dict = None
    info_selection = pn.widgets.Select(name='Info header', options=[], visible=False, value='')
    info_selected_value = pn.pane.Str('')
    ready = param.Boolean(default=True)

    @pn.depends('sampling_rate_input.value', watch=True)
    def set_sampling_rate_value(self):
        self.ready = False
        if not self.sampling_rate_input.value:
            return
        try:
            self.sampling_rate = float(self.sampling_rate_input.value)
            self.ready = True
        except ValueError:
            pn.state.notifications.error('Sampling rate must be a number (seperated by a .)')

    @pn.depends('info_selection.value', watch=True)
    def display_info_value(self):
        if not self.info_selection.value or self.info_selection.value not in self.info_dict.keys():
            self.info_selected_value.object = ''
        else:
            self.info_selected_value.object = self.info_dict[self.info_selection.value]

    @param.output(('original_data', param.Dynamic), ('sampling_rate', param.Dynamic))
    def output(self):
        return self.data, self.sampling_rate

    def get_session_start_and_end(self, pane):
        start = pn.widgets.DatetimePicker(name='Session start:',
                                          disabled=True)
        end = pn.widgets.DatetimePicker(name='Session end:',
                                        disabled=True)
        if type(self.data) == pd.DataFrame:
            start_end = get_start_and_end_time(self.data)
            if start_end is None:
                pn.state.notifications.error("Error: Failure at searching for start and end time.")
                return
            start.value = start_end[0]
            end.value = start_end[1]
        elif type(self.data) == Session:
            start.value = self.data.info.local_datetime_start[0]
            end.value = self.data.info.local_datetime_stop[0]
        if type(self.data) != SyncedSession:
            pane.append(start)
            pane.append(end)
            return pane
        elif type(self.data) == SyncedSession:
            pane.append(pn.widgets.StaticText(name='Info', value=self.data.info))
            for dataset in self.data.datasets:
                pane.append(pn.widgets.StaticText(name='Session info:', value=dataset.info))
                pane.append(pn.widgets.DataFrame(name='Session', value=dataset.data_as_df().head(20)))
            return pane

    def panel(self):
        if self.text == "":
            f = open('../assets/Markdown/ECG_FilesUploaded.md', 'r')
            fileString = f.read()
            self.text = fileString
        pane = pn.Column(
            pn.pane.Markdown(self.text)
        )

        if self.sampling_rate == -1 or type(self.data) == pd.DataFrame:
            if self.sampling_rate != -1:
                self.sampling_rate_input.value = str(self.sampling_rate)
            pane.append(self.sampling_rate_input)
            if self.sampling_rate_input.value == '':
                self.ready = False
            else:
                self.ready = True

        pane = self.get_session_start_and_end(pane)
        if type(self.data) == pd.DataFrame:
            pane.append(pn.widgets.DataFrame(name='Data', value=self.data.head(100)))
        elif type(self.data) == Session:
            pane.append(pn.widgets.DataFrame(name='Session', value=self.data.data_as_df()[0].head(20)))
        return pane

