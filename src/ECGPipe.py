import panel as pn
import param
import io
from nilspodlib import Session, SyncedSession

from AdaptedNilspod import *
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
    timezone_Select = pn.widgets.Select(name='Timezone', options=['None Selected']+ pytz.all_timezones,
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

    @param.output(('data', param.Dynamic), ('sampling_rate', param.Dynamic), ('synced', param.Boolean), ('session_type', param.String))
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


# TODO: noch die niedrigste und die höchste Zeit herausfinden
class DataArrived(param.Parameterized):
    synced = param.Boolean()
    session_type = param.String()
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    sampling_rate_input = pn.widgets.TextInput(name='Sampling rate Input', placeholder='Enter your sampling rate here...')
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
            datetime_columns = self.get_datetime_columns_of_data_frame()
            if len(datetime_columns) == 0 or len(datetime_columns) > 1:
                print(datetime_columns)
            #Hier muss noch eine Column angegeben werden die convertiert werden muss
            elif len(datetime_columns) == 1:
                print(datetime_columns)
                #Perfekt hier gibt es nur eine Möglichkeit


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

    def get_datetime_columns_of_data_frame(self):
        df_type = self.data.dtypes.rename_axis('column')\
            .to_frame('dtype')\
            .reset_index(drop=False)
        df_type['dtype_str'] = df_type['dtype'].map(str)
        return df_type[df_type['dtype_str'].str.contains('datetime64')]['column'].tolist()

# TODO: Start und stopp Zeiten nach unten bzw. oben limitieren, Daten cutten --> müssen hierzu alle in df umgewandelt werden? (zwar cut fkt bei nilspodlib aber nur index basiert)
class TrimSession(param.Parameterized):
    data = param.Dynamic()
    sampling_rate = param.Dynamic()
    text = ''
    start_time = pn.widgets.DatetimePicker(name='Start time')
    stop_time = pn.widgets.DatetimePicker(name='Stop time')

    def panel(self):
        if self.text == "":
            f = open('../assets/Markdown/EditStartAndStopTimes.md', 'r')
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.start_time,
            self.stop_time
        )


#TODO: Outlier Detection, Processing + Preview, Welche Subtypen (Ankreuzfelder), Finish + Results runterladen (DF HR und HV + Plots optional auch, als .zip File)
class ECGPipeline:
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage("Session Kind", SessionKind(), ready_parameter='ready')
        self.pipeline.add_stage("File Upload", FileUploadPhysiological(), ready_parameter='ready')
        self.pipeline.add_stage("Data arrived", DataArrived(), ready_parameter='ready')
        self.pipeline.add_stage("Trim Session", TrimSession())
