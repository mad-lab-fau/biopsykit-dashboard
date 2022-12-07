importScripts("https://cdn.jsdelivr.net/pyodide/v0.21.3/full/pyodide.js");

function sendPatch(patch, buffers, msg_id) {
  self.postMessage({
    type: 'patch',
    patch: patch,
    buffers: buffers
  })
}

async function startApplication() {
  console.log("Loading pyodide!");
  self.postMessage({type: 'status', msg: 'Loading pyodide'})
  self.pyodide = await loadPyodide();
  self.pyodide.globals.set("sendPatch", sendPatch);
  console.log("Loaded!");
  await self.pyodide.loadPackage("micropip");
  const env_spec = ['https://cdn.holoviz.org/panel/0.14.1/dist/wheels/bokeh-2.4.3-py3-none-any.whl', 'https://cdn.holoviz.org/panel/0.14.1/dist/wheels/panel-0.14.1-py3-none-any.whl', 'pyodide-http==0.1.0', 'AdaptedNilspod', 'biopsykit', 'io', 'numpy', 'pandas', 'param', 'pytz']
  for (const pkg of env_spec) {
    let pkg_name;
    if (pkg.endsWith('.whl')) {
      pkg_name = pkg.split('/').slice(-1)[0].split('-')[0]
    } else {
      pkg_name = pkg
    }
    self.postMessage({type: 'status', msg: `Installing ${pkg_name}`})
    try {
      await self.pyodide.runPythonAsync(`
        import micropip
        await micropip.install('${pkg}');
      `);
    } catch(e) {
      console.log(e)
      self.postMessage({
	type: 'status',
	msg: `Error while installing ${pkg_name}`
      });
    }
  }
  console.log("Packages loaded!");
  self.postMessage({type: 'status', msg: 'Executing code'})
  const code = `
  
import asyncio

from panel.io.pyodide import init_doc, write_doc

init_doc()

import panel as pn
pn.extension(sizing_mode='stretch_width')
pn.extension(notifications=True)
pn.extension('plotly', 'tabulator')
#micropip.install('biopsykit')
import biopsykit as bp
#from MainPage import *
import panel as pn
pn.extension(sizing_mode='stretch_width')
pn.extension(notifications=True)
pn.extension('plotly', 'tabulator')
#from ECGPipe import *
import numpy as np
import panel as pn
import param
import io
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
    sessionType_Select = pn.widgets.Select(name='Session Type', options=['Multi Session', 'Single Session'])
    timezone_Select = pn.widgets.Select(name='Timezone', options=['None Selected'] + pytz.all_timezones)
    text = ''
    ready = param.Boolean(default=False)

    @param.depends('timezone_Select.value', watch=True)
    def timezone_selected(self):
        if self.timezone_Select.value != 'None Selected':
            setattr(self, 'ready', True)
        else:
            setattr(self, 'ready', False)

    @param.output(('sessionType', param.String), ('synced', param.Boolean), ('timezone', param.String))
    def output(self):
        if self.synced_RadioBox.value == 'Synced':
            return self.sessionType_Select.value, True, self.timezone_Select.value
        else:
            return self.sessionType_Select.value, False, self.timezone_Select.value

    @param.depends('sessionType_Select.value', watch=True)
    def panel(self):
        if self.text == "":
            f = open('../Assets/Markdown/FirstPagePhysiologicalData.md', 'r')
            fileString = f.read()
            self.text = fileString
        if self.sessionType_Select.value == 'Multi Session':
            self.synced_RadioBox.disabled = False
            return pn.Column(
                pn.pane.Markdown(self.text),
                self.timezone_Select,
                self.sessionType_Select,
                self.synced_RadioBox
            )
        else:
            self.synced_RadioBox.disabled = True
            return pn.Column(
                pn.pane.Markdown(self.text),
                self.timezone_Select,
                self.sessionType_Select
            )


class FileUploadPhysiological(param.Parameterized):
    text = ''
    file_input = pn.widgets.FileInput(background='WhiteSmoke', multiple=False, accept='.csv,.bin')
    file_clientside = ClientSideDirectoryInput()
    sessionType = param.String()
    synced = param.Boolean()
    timezone = param.String()
    ready = param.Boolean(default=False)
    data = None
    sampling_rate = -1

    @pn.depends("file_clientside.value", watch=True)
    def _parse_file_input(self):
        print('Parsing started')
        print(self.file_clientside.value)
        print('after value print')
        value = self.file_clientside.value
        if self.sessionType == 'Multi Session':
            print('Multi Session DirHandle')
            return
        if value is not None or len(value) > 0:
            if self.file_clientside.fileName.endswith('.bin'):
                if self.d:
                    print("Synced not yet implemented")
                else:
                    self.handle_bin_file_not_synced(bytefile=value)
                    pn.state.notifications.success(self.file_clientside.fileName)
            else:
                if self.file_clientside.fileName.endswith('.csv'):
                    self.handle_csv_file(bytefile=value)
                else:
                    pn.state.notifications.error('Not a matching file format')
                    return
            self.ready = True
        else:
            print("Error: No value")

    def handle_bin_file_not_synced(self, bytefile: np.ndarray):
        dataset = NilsPodAdapted.from_bin_file(byteFile=bytefile, legacy_support='resolve', tz='Europe/Berlin')
        self.data, self.sampling_rate = bp.io.nilspod.load_dataset_nilspod(dataset=dataset, timezone='Europe/Berlin')

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

    @param.output(('c', param.String), ('d', param.Boolean))
    def output(self):
        return self.data

    def view(self):
        if self.sessionType == 'Multi Session':
            self.file_clientside = ClientSideDirectoryInput()
        else:
            self.file_clientside = ClientSideFileInput()
        if self.text == "":
            f = open('../Assets/Markdown/PhysiologicalFileUpload.md', 'r')
            fileString = f.read()
            self.text = fileString
        return pn.Column(
            pn.pane.Markdown(self.text),
            self.file_clientside
        )

    def panel(self):
        return pn.Row(self.view)


class ECGPipeline():
    pipeline = None

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline(debug=True)
        self.pipeline.add_stage("Session Kind", SessionKind(), ready_parameter='ready')
        self.pipeline.add_stage("File Upload", FileUploadPhysiological(), ready_parameter='ready')


class MainPage(param.Parameterized):
    welcomeText = ""
    signalSelection = pn.GridBox(ncols=3)
    physBtn = pn.widgets.Button(name="Physiological Data")
    sleepBtn = pn.widgets.Button(name="Sleep Data")
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data")
    psychBtn = pn.widgets.Button(name="Psychological Data")
    salBtn = pn.widgets.Button(name="Saliva Data")
    mainPage = None

    def startPhysPipeline(self, event):
        ecg = ECGPipeline()
        return self.mainPage.append(ecg.pipeline)

    def __init__(self, mainPage, **params):
        f = open('../Assets/Markdown/WelcomeText.md', 'r')
        fileString = f.read()
        self.mainPage = mainPage
        self.welcomeText = fileString
        self.physBtn.on_click(self.startPhysPipeline)
        self.signalSelection.append(self.physBtn)
        super().__init__(
            **params)

    def view(self):
        # ecg = ECGPipeline()
        # return ecg.pipeline
        return pn.Column(
            pn.pane.Markdown(self.welcomeText),
            self.signalSelection
        )







app = pn.template.FastListTemplate(title='BioPysKit Dashboard', header_background='#186FEF',
                                   logo='../Aassets/biopsykit_Icon.png',
                                   favicon="/favicon.ico")
app.sidebar.constant = False
app.main.constant = False
app.theme_toggle = False
current_page = pn.Column()
current_page = MainPage(app.main)

def startPhysPipeline(event):
    ecg = ECGPipeline()
    pane = pn.Column(
        pn.Row(ecg.pipeline.title, pn.layout.HSpacer(), ecg.pipeline.buttons),
        ecg.pipeline.stage
    )
    app.main[0].objects = [pane]


def get_sidebar():
    homeBtn = pn.widgets.Button(name='Home', button_type='primary')
    homeBtn.on_click(get_mainMenu)
    physBtn = pn.widgets.Button(name='Physiological Data')
    physBtn.on_click(startPhysPipeline)
    psychBtn = pn.widgets.Button(name='Psychological Data')
    sleepBtn = pn.widgets.Button(name='Sleep Data')
    salBtn = pn.widgets.Button(name="Saliva Data")
    column = pn.Column(
        homeBtn,
        physBtn,
        psychBtn,
        sleepBtn,
        salBtn
    )
    return column

def get_mainMenu(event):
    f = open('../Assets/Markdown/WelcomeText.md', 'r')
    fileString = f.read()
    physBtn = pn.widgets.Button(name="Physiological Data", sizing_mode='stretch_width', align='end')
    physBtn.on_click(startPhysPipeline)
    sleepBtn = pn.widgets.Button(name="Sleep Data", sizing_mode='stretch_width', align='end')
    questionnaireBtn = pn.widgets.Button(name="Questionnaire Data", sizing_mode='stretch_width')
    psychBtn = pn.widgets.Button(name="Psychological Data", sizing_mode='stretch_width')
    salBtn = pn.widgets.Button(name="Saliva Data", sizing_mode='stretch_width')
    pathToIcons = "../Icons/"
    iconNames = ['Physiological.svg', 'Psychological.svg', 'Questionnaire.svg', 'Saliva.svg', 'Sleep.svg']
    physCard = pn.Card(
        pn.pane.SVG(pathToIcons + iconNames[0], align='center', sizing_mode='stretch_both', max_height=150,
                    max_width=200, background='whitesmoke'), pn.Spacer(height=45), physBtn, collapsible=False,
        height=250, background='whitesmoke', hide_header=True)
    psychCard = pn.Card(
        pn.pane.SVG(pathToIcons + iconNames[1], align='center', sizing_mode='stretch_both', max_height=150,
                    max_width=150, background='whitesmoke'), pn.Spacer(height=45), psychBtn, collapsible=False,
        height=250, background='whitesmoke', hide_header=True)
    questionnaireCard = pn.Card(
        pn.pane.SVG(pathToIcons + iconNames[2], align='center', sizing_mode='stretch_both', max_height=150,
                    max_width=150, background='whitesmoke'), pn.Spacer(height=45), questionnaireBtn, collapsible=False,
        height=250, background='whitesmoke', hide_header=True)
    salCard = pn.Card(
        pn.pane.SVG(pathToIcons + iconNames[3], align='center', sizing_mode='stretch_both', max_height=150,
                    max_width=150, background='whitesmoke'), pn.Spacer(height=45), salBtn, collapsible=False,
        height=250, background='whitesmoke', hide_header=True)
    sleepCard = pn.Card(
        pn.pane.SVG(pathToIcons + iconNames[4], align='center', sizing_mode='stretch_both', max_height=150,
                    max_width=160, background='whitesmoke'), pn.Spacer(height=45), sleepBtn, collapsible=False,
        height=250, background='whitesmoke', hide_header=True)
    signalSelection = pn.GridBox(*[physCard, psychCard, questionnaireCard, salCard, sleepCard], ncols=3)
    pane = pn.Column(
        pn.pane.Markdown(fileString),
        signalSelection
    )
    if len(app.main) > 0:
        app.main[0].objects = [pane]
    else:
        app.main.append(pane)

app.sidebar.append(get_sidebar())
get_mainMenu(None)
app.servable();

# def main():
#     app.sidebar.append(get_sidebar())
#     get_mainMenu(None)
#     app.servable().show()
#     #app.show()
#
# if __name__ == "__main__":
#     main()

await write_doc()
  `

  try {
    const [docs_json, render_items, root_ids] = await self.pyodide.runPythonAsync(code)
    self.postMessage({
      type: 'render',
      docs_json: docs_json,
      render_items: render_items,
      root_ids: root_ids
    })
  } catch(e) {
    const traceback = `${e}`
    const tblines = traceback.split('\n')
    self.postMessage({
      type: 'status',
      msg: tblines[tblines.length-2]
    });
    throw e
  }
}

self.onmessage = async (event) => {
  const msg = event.data
  if (msg.type === 'rendered') {
    self.pyodide.runPythonAsync(`
    from panel.io.state import state
    from panel.io.pyodide import _link_docs_worker

    _link_docs_worker(state.curdoc, sendPatch, setter='js')
    `)
  } else if (msg.type === 'patch') {
    self.pyodide.runPythonAsync(`
    import json

    state.curdoc.apply_json_patch(json.loads('${msg.patch}'), setter='js')
    `)
    self.postMessage({type: 'idle'})
  } else if (msg.type === 'location') {
    self.pyodide.runPythonAsync(`
    import json
    from panel.io.state import state
    from panel.util import edit_readonly
    if state.location:
        loc_data = json.loads("""${msg.location}""")
        with edit_readonly(state.location):
            state.location.param.update({
                k: v for k, v in loc_data.items() if k in state.location.param
            })
    `)
  }
}

startApplication()