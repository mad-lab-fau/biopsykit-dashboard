from datetime import datetime, timedelta

import panel as pn
import param
import io
from nilspodlib import Session, SyncedSession
from AdaptedNilspod import *
from src.utils import get_datetime_columns_of_data_frame, timezone_aware_to_naive

pn.extension(sizing_mode='stretch_width')
pn.extension(notifications=True)
pn.extension('plotly', 'tabulator')
from biopsykit.signals.ecg import EcgProcessor
import pandas as pd
import biopsykit as bp

pn.extension('katex')
from panel.reactive import ReactiveHTML
import pytz


class ClientSideFileInput(ReactiveHTML):
    fileContent = None
    value = param.Array()
    fileName = param.String()

    _template = """
        <input type="file" id="input" onclick='${script("select")}' />
    """

    _scripts = {
        'render': """
        """,
        'select': """
            // store a reference to our file handle
            let fileHandle;
            const options = {
                multiple: true,
                types: [
                    {
                        description: 'Files to analyze',
                        accept: {
                        'text/plain': ['.bin','.csv','.xlsx'],
                        },
                    },
                ],
            };
            async function getFile() {        
                [fileHandle] = await window.showOpenFilePicker(options);           
                
                if (fileHandle.kind === 'file') {
                    //run file code
                    
                    const file = await fileHandle.getFile();
                    //console.log(file);
                    let contents = await file.arrayBuffer(); 
                    let arr = new Uint8Array(contents);
                    //console.log(arr);
                    data.value = arr;
                    data.fileName = fileHandle.name;
                }
              
            }

            getFile();
        """
    }


class ClientSideDirectoryInput(ReactiveHTML):
    fileContent = None
    value = param.Array()
    fileName = param.String()
    directoryName = param.String()

    _template = """
        <input type="file" id="input" onclick='${script("select")}' />
    """

    _scripts = {
        'render': """
        """,
        'select': """
            async function getFiles() {   
                // store a reference to our file handle
                const dirHandle = await window.showDirectoryPicker();
                const promises = [];
                for await (const entry of dirHandle.values()) {
                    if (entry.kind !== 'file') {
                        continue;
                    }
                    
                    const file = await entry.getFile();
                    let fileName = file.name;
                    if(fileName.endsWith('.bin') || fileName.endsWith('.csv')){
                        console.log(fileName);
                        let contents = await file.arrayBuffer(); 
                        let arr = new Uint8Array(contents);
                        const data = {
                            name: fileName,
                            fileContent: arr 
                        };
                        promises.push(data);
                    }

                }
                console.log(await Promise.all(promises));        
                data.value = promises;      
            }
            getFiles();
            console.log('Done');
        """
    }


class SessionKind(param.Parameterized):
    synced_RadioBox = pn.widgets.RadioBoxGroup(name='Synced', options=['Synced', 'Not Synced'])
    session_type_Select = pn.widgets.Select(name='Session Type', options=['Multi Session', 'Single Session'])
    timezone_Select = pn.widgets.Select(name='Timezone', options=['None Selected'] + pytz.all_timezones,
                                        value='Europe/Berlin')
    text = ''
    ready = param.Boolean(default=False)

    @param.depends('timezone_Select.value', watch=True)
    def timezone_selected(self):
        if self.timezone_Select.value != 'None Selected':
            setattr(self, 'ready', True)
        else:
            setattr(self, 'ready', False)

    @param.output(('session_type', param.String), ('synced', param.Boolean), ('timezone', param.String))
    def output(self):
        if self.synced_RadioBox.value == 'Synced':
            return self.session_type_Select.value, True, self.timezone_Select.value
        else:
            return self.session_type_Select.value, False, self.timezone_Select.value

    @param.depends('session_type_Select.value', watch=True)
    def panel(self):
        if self.text == "":
            f = open('../assets/Markdown/FirstPagePhysiologicalData.md', 'r')
            fileString = f.read()
            self.text = fileString
        if self.session_type_Select.value == 'Multi Session':
            self.synced_RadioBox.disabled = False
        else:
            self.synced_RadioBox.disabled = True
        self.ready = True
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.timezone_Select,
            self.session_type_Select,
            self.synced_RadioBox
        )


class FileUploadPhysiological(param.Parameterized):
    text = ''
    filetype_Select = pn.widgets.Select(name='File Type', options=['Multi Session', 'Single Session'])
    file_input = pn.widgets.FileInput(background='WhiteSmoke', multiple=False, accept='.csv,.bin')
    session_type = param.String()
    synced = param.Boolean()
    timezone = param.String()
    ready = param.Boolean(default=False)
    data = None
    sampling_rate = param.Dynamic(default=-1)

    @pn.depends("file_input.value", watch=True)
    def _parse_file_input(self):
        self.ready = False
        self.data = None
        value = self.file_input.value
        if value is not None or len(value) > 0:
            if type(self.file_input.value) == list and not self.synced:
                for val, fn in zip(self.file_input.value, self.file_input.filename):
                    self.handle_single_file(io.BytesIO(val), fn)
                self.data = Session(self.data)
                self.ready = True
            elif type(self.file_input.value) == list and self.synced:
                for val, fn in zip(self.file_input.value, self.file_input.filename):
                    self.handle_single_file(io.BytesIO(val), fn)
                self.data = SyncedSession(self.data)
                self.ready = True
            elif type(self.file_input.value) != list:
                self.handle_single_file(self.file_input.value, self.file_input.filename)
                if self.file_input.filename.endswith('.bin'):
                    self.data = Session(self.data)
                self.ready = True
            else:
                pn.state.notifications.error("No matching operators")
        else:
            pn.state.notifications.error("No matching operators")

    def handle_single_file(self, value, filename):
        if filename.endswith('.bin'):
            self.handle_bin_file(bytefile=BytesIO(value))
            pn.state.notifications.success(filename)
        elif filename.endswith('.csv'):
            if self.file_input.filename.endswith('.csv'):
                self.handle_csv_file(bytefile=value)
        else:
            pn.state.notifications.error('Not a matching file format')

    def handle_bin_file(self, bytefile: bytes):
        dataset = NilsPodAdapted.from_bin_file(file=bytefile, legacy_support='resolve', tz=self.timezone)
        if self.data is None:
            self.data = []
        self.data.append(dataset)

    def handle_csv_file(self, bytefile: bytes):
        string_io = io.StringIO(bytefile.decode("utf8"))
        self.data = pd.read_csv(string_io, parse_dates=["time"])
        if self.data is None:
            pn.state.notifications.error('Empty csv File arrived', duration=10000)
        if "ecg" not in self.data.columns:
            pn.state.notifications.error('Uploaded csv File misses the column ecg', duration=10000)
            return
        if "time" not in self.data.columns:
            pn.state.notifications.error('Uploaded csv File misses the column time', duration=10000)
            return
        self.data['ecg'] = self.data['ecg'].astype(float)
        pn.state.notifications.success('File uploaded successfully', duration=5000)

    def set_timezone_of_datetime_columns_(self):
        datetime_columns = get_datetime_columns_of_data_frame(self.data)
        for col in datetime_columns:
            self.data[col] = self.data[col].dt.tz_localize(self.timezone)

    @param.output(('data', param.Dynamic), ('sampling_rate', param.Dynamic), ('synced', param.Boolean),
                  ('session_type', param.String))
    def output(self):
        return self.data, self.sampling_rate, self.synced, self.session_type

    def view(self):
        if self.session_type == 'Multi Session':
            self.file_input.multiple = True
        if self.text == "":
            f = open('../assets/Markdown/PhysiologicalFileUpload.md', 'r')
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.file_input
        )

    def panel(self):
        return pn.Row(self.view)


# TODO: noch die niedrigste und die höchste Zeit herausfinden, ready noch in panel Func anpassen
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

    def panel(self):
        if self.text == "":
            f = open('../assets/Markdown/ECG_FilesUploaded.md', 'r')
            fileString = f.read()
            self.text = fileString
        pane = pn.Column(
            pn.pane.Markdown(self.text)
        )
        if type(self.data) == pd.DataFrame:
            pane.append(self.sampling_rate_input)
            datetime_columns = get_datetime_columns_of_data_frame(self.data)
            if len(datetime_columns) == 0 or len(datetime_columns) > 1:
                pn.state.notifications.error("In the dataframe is more than one Datetime Column")
                self.ready = False
            elif len(datetime_columns) == 1:
                pane.append(
                    pn.widgets.DatetimePicker(name='Session start:', value=self.data[datetime_columns[0]].min()
                                              , disabled=True))
                pane.append(pn.widgets.DatetimePicker(name='Session end:', value=self.data[datetime_columns[0]].max()
                                                      , disabled=True))
            pane.append(pn.widgets.DataFrame(name='Data', value=self.data.head(100)))
            self.ready = False
        elif type(self.data) == SyncedSession:
            pane.append(pn.widgets.StaticText(name='Info', value=self.data.info))
            for dataset in self.data.datasets:
                pane.append(pn.widgets.StaticText(name='Session info:', value=dataset.info))
                pane.append(pn.widgets.DataFrame(name='Session', value=dataset.data_as_df().head(20)))
        elif type(self.data) == Session:
            pane.append(pn.widgets.DatetimePicker(name='Session start:', value=self.data.info.local_datetime_start[0]
                                                  , disabled=True))
            pane.append(pn.widgets.DatetimePicker(name='Session end:', value=self.data.info.local_datetime_stop[0]
                                                  , disabled=True))
            pane.append(self.info_selection)
            pane.append(self.info_selected_value)
            pane.append(pn.widgets.DataFrame(name='Session', value=self.data.data_as_df()[0].head(20)))
        return pane


# TODO: Start und stopp Zeiten nach unten bzw. oben limitieren, Daten cutten --> müssen hierzu alle in df umgewandelt werden? (zwar cut fkt bei nilspodlib aber nur index basiert)
class TrimSession(param.Parameterized):
    original_data = param.Dynamic()
    trimmed_data = param.Dynamic()
    sampling_rate = param.Dynamic()
    text = ''
    start_time = pn.widgets.DatetimePicker(name='Start time')
    stop_time = pn.widgets.DatetimePicker(name='Stop time')
    trim_btn = pn.widgets.Button(name='Trim', button_type='primary')
    min_time = None
    max_time = None

    def limit_times(self):
        if type(self.original_data) is pd.DataFrame:
            dt_cols = get_datetime_columns_of_data_frame(self.original_data)
            if len(dt_cols) != 1:
                pn.state.notifications("Error: Not exactly one Datetime Column in Dataframe")
                return

            start, end = min(self.original_data[dt_cols[0]]), max(self.original_data[dt_cols[0]])
            self.min_time = timezone_aware_to_naive(start)
            self.max_time = timezone_aware_to_naive(end)
            self.start_time.start = self.min_time
            self.start_time.end = self.max_time
            self.stop_time.start = self.min_time
            self.stop_time.end = self.max_time
            self.start_time.value = self.min_time
            self.stop_time.value = self.max_time

    @pn.depends('start_time.value', watch=True)
    def start_time_changed(self):
        if self.stop_time.value is None or self.start_time.value is None:
            return
        if self.stop_time.value < self.start_time.value:
            self.stop_time.value = self.start_time.value
            pn.state.notifications.warning("Stop time is lower than the selected start time!")

    @pn.depends('stop_time.value', watch=True)
    def stop_time_changed(self):
        if self.stop_time.value is None or self.start_time.value is None:
            return
        if self.stop_time.value < self.start_time.value:
            self.start_time.value = self.stop_time.value
            pn.state.notifications.warning("s time is lower than the selected start time!")

    '''TODO: Trim the data to the new span, and keep the original data 
    (Two cases: CSV or bin --> hier evtl. noch unterscheidung zwischen synced und nicht snyced)'''

    def trim_data(self, event):
        print('Trim started')
        print(self.trim_btn.clicks)
        if type(self.original_data) is pd.DataFrame:
            print('trim df')
            dt_col = get_datetime_columns_of_data_frame(self.original_data)
            if len(dt_col) == 1:
                col = dt_col[0]
                start = self.start_time.value
                stop = self.stop_time.value
                tz = pytz.timezone('Europe/Berlin')
                start = tz.localize(start)
                stop = tz.localize(stop)
                self.trimmed_data = self.original_data.loc[(self.original_data[col] >= start)
                                                           & (self.original_data[col] <= stop)]
        else:
            print('session')

    def panel(self):
        self.trim_btn.on_click(self.trim_data)
        self.trimmed_data = self.original_data
        self.limit_times()
        if self.text == "":
            f = open('../assets/Markdown/EditStartAndStopTimes.md', 'r')
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.start_time,
            self.stop_time,
            self.trim_btn
        )

    @param.output(('data', param.Dynamic), ('sampling_rate', param.Dynamic))
    def output(self):
        return self.trimmed_data, self.sampling_rate


class OutlierDetection(param.Parameterized):
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    textHeader = ''
    textParams = ''
    methods = ['quality',
               'artifact',
               'physiological',
               'statistical_rr',
               'statistical_rr_diff']

    outlier_methods = pn.widgets.MultiChoice(name='Methods', value=['quality', 'artifact'], options=methods)
    statistical_param = pn.widgets.FloatInput(name='Statistical:', value=2.576)
    ecg_processor = None
    correlation = pn.widgets.FloatInput(name='correlation', value=0.3)
    quality = pn.widgets.FloatInput(name='quality', value=0.4)
    artifact = pn.widgets.FloatInput(name='artifact', value=0)
    statistical_rr = pn.widgets.FloatInput(name='statistical_rr', value=2.576)
    statistical_rr_diff = pn.widgets.FloatInput(name='statistical_rr_diff', value=1.96)
    physiological_upper = pn.widgets.FloatInput(name='physiological_upper', value=200)
    physiological_lower = pn.widgets.FloatInput(name='physiological_lower', value=45)

    def panel(self):
        self.ecg_processor = EcgProcessor(data=self.data, sampling_rate=self.sampling_rate)
        if self.textHeader == "":
            f = open('../assets/Markdown/OutlierDetection.html', 'r')
            fileString = f.read()
            self.textHeader = fileString
        if self.textParams == "":
            f = open('../assets/Markdown/OutlierParams.md', 'r')
            fileString = f.read()
            self.textParams = fileString
        return pn.Column(
            pn.pane.HTML(self.textHeader),
            self.outlier_methods,
            pn.pane.Markdown(self.textParams),
            self.correlation,
            self.quality,
            self.artifact,
            self.statistical_rr,
            self.statistical_rr_diff,
            pn.Row(
                self.physiological_lower,
                self.physiological_upper
            )
        )

    def get_outlier_params(self):
        return {
            'correlation': self.correlation.value,
            'quality': self.quality.value,
            'artifact': self.artifact.value,
            'statistical_rr': self.statistical_rr.value,
            'statistical_rr_diff': self.statistical_rr_diff,
            'physiological': (self.physiological_lower.value, self.physiological_upper.value)
        }

    @param.output(('ecg_processor', param.Dynamic))
    def output(self):
        self.ecg_processor.ecg_process(outlier_correction=self.outlier_methods.value,
                                       outlier_params=self.get_outlier_params())
        return self.ecg_processor


class ProcessingAndPreview(param.Parameterized):
    ecg_processor = param.Dynamic()
    textHeader = ''
    # Dataframes in Accordion

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

# TODO: Welche Subtypen (Ankreuzfelder), Finish + Results runterladen (DF HR und HV + Plots optional auch, als .zip File)
class ECGPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage("Session Kind", SessionKind(), ready_parameter='ready')
        self.pipeline.add_stage("File Upload", FileUploadPhysiological(), ready_parameter='ready')
        self.pipeline.add_stage("Data arrived", DataArrived(), ready_parameter='ready')
        self.pipeline.add_stage("Trim Session", TrimSession())
        self.pipeline.add_stage("Outlier Processing", OutlierDetection())
        self.pipeline.add_stage("Preview", ProcessingAndPreview())
        self.pipeline.add_stage('Process HRV', ProcessHRV())
