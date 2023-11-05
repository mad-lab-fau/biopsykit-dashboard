# How to contribute


This part of the documentation explains how to further develop parts of Biopsykit - Dashboard and how the project
is structured. 

The Project contains out of the following main parts:

<ul>
   <li>src</li>
   <li>tests</li>
   <li>convert_files.py</li>
   <li>main.py</li>
   <li>main_ide</li>
   <li>single_pipeline.py</li>
</ul>

## Contents of src

The src folder contains all the different pipelines as separate Python packages as well as the main page. Each package 
contains an _init_.py file, a CONSTANTS file, a pipeline file and files for the different steps of the pipeline. 
The CONSTANTS Files contain the constants of the different pipelines. Important parts are here the maximum amount 
of steps, as well as the Markdown text used in the different steps (so if you want to change the description of a 
pipeline step you can do that in the CONSTANTS file of the corresponding pipeline). In the pipeline file the different 
steps are defined and also their order. In this pipeline files the different panel pages are imported and added to the 
pipeline.


### Constants

One short example for a constant file is the following:

```python
SLEEP_MAX_STEPS = 7

POSSIBLE_DEVICES = [
    "Polysomnography",
    "Other IMU Device",
    "Withings",
]

UPLOAD_PARAMETERS_TEXT = "# Set sleep data parameters \n Below you can set the parameters for the sleep data. If you are unsure, you can leave the default values."
CHOOSE_DEVICE_TEXT = "# Choose the recording device \n Below you can choose the device you used to record your sleep data. If you used a different device, please choose 'Other IMU Device'."
ZIP_OR_FOLDER_TEXT = "# File or Folder? \n If you want to upload a complete folder, please zip it first. You can then upload the zip file in the following step."
UPLOAD_SLEEP_DATA_TEXT = "# Upload your sleep data \n Please upload your sleep data in the following step. You can either upload a single file or a zip file containing all your files."
```
As you can see, you can easily define the maximum amount of steps this pipeline has, as well as the text for the 
different steps. But there are other constants defined here, like the possible devices.

### Pipeline

These files manage the different steps of the pipeline as well as their order. The following is an example of a pipeline file:

```python
class SalivaPipeline:
    pipeline = None
    name = "Saliva"

    def __init__(self):
        self.pipeline = pn.pipeline.Pipeline()
        self.pipeline.add_stage(
            "Ask for Format",
            AskForFormat(),
            **{"ready_parameter": "ready", "auto_advance": True},
        )
        self.pipeline.add_stage(
            "Ask for Subject Condition List",
            AskToLoadConditionList(),
            **{
                "ready_parameter": "ready",
                "auto_advance": True,
                "next_parameter": "next_page",
            },
        )
        self.pipeline.add_stage(
            "Add Condition List",
            AddConditionList(),
            **{"ready_parameter": "ready"},
        )
        self.pipeline.add_stage(
            "Load Saliva Data",
            LoadSalivaData(),
        )
        self.pipeline.add_stage("Show Features", ShowSalivaFeatures())

        self.pipeline.define_graph(
            {
                "Ask for Format": "Ask for Subject Condition List",
                "Ask for Subject Condition List": (
                    "Add Condition List",
                    "Load Saliva Data",
                ),
                "Add Condition List": "Load Saliva Data",
                "Load Saliva Data": "Show Features",
            }
        )
```

This object has two fields: a pipeline object and a name. The pipeline object is a pn.pipeline.Pipeline() object and 
the name is just a string. The name is used if you want to build a single pipeline as a standalone page (to better 
indicate which data this pipeline analyses). The pipeline object is initialized in the constructor of the class.
The different steps are added to the pipeline object with the
[add_stage() method](https://panel.holoviz.org/api/panel.pipeline.html#panel.pipeline.Pipeline.add_stage) . 
The first parameter is the name of the step which is displayed at the top right of the page. The second parameter is 
a panel object which is the actual content of the step, these classes are defined in the rest of the matching pipeline package.
The third parameter is a dictionary with the different parameters of the step. The most important parameters are:

<ul>
   <li><strong>ready_parameter:</strong> Here you can set which field of the class is responsible as the ready parameter 
      if this value is false the user can't progress to the next step</li>
   <li><strong>auto_advance:</strong> If this is set to true, the user progresses to the next step as soon as the 
      <strong>ready_parameter</strong> becomes true without clicking "Next"</li>
   <li><strong>next_parameter:</strong> This parameter indicates the name of the field which is responsible for the 
      next page. If this is set, it is possible to influence the order of steps (so which step comes after the current one)</li>
</ul>

The last important point in the pipeline classes is the definition of the graph. This is done with the 
[define_graph() method](https://panel.holoviz.org/api/panel.pipeline.html#panel.pipeline.Pipeline.define_graph). 
This Method gets a dictionary as a parameter. The keys of the dictionary are the names of the steps and the values are 
the following step(s). If there is only one value, the next step is always this step. For example after the 
"Ask for Format" step the next step is always the "Ask for Subject Condition List" step. Therefore, the Dictionary 
entry looks like this: 
```python
 "Ask for Format": "Ask for Subject Condition List"
```
So you can see the key is always the name of the step and the value is the name of the next step. If there are multiple 
possibles steps which can follow directly after the current step, the value is a tuple of the possible steps. 
For example after the "Ask for Subject Condition List" step the next step can be either the "Add Condition List" step or
the "Load Saliva Data" step. Therefore, the Dictionary entry looks like this: 
```python
 "Ask for Subject Condition List": ("Add Condition List", "Load Saliva Data")
```

> **Important**
>
> The order of the steps is defined in the graph definition. Also the names of the steps are defined in the graph are case sensitive.
>
{style="note"}

With this information you should be able to understand the different pipelines and also create new ones. Now we can take
a look how to define a single step in the pipeline and afterward how to make that pipeline accessible in the main page.

### Step of a pipeline

The steps of a pipeline are defined in the different files in the pipeline package. The following is simple 
example of a step:

```python
import param
import panel as pn

from src.Saliva.SALIVA_CONSTANTS import ASK_FOR_FORMAT_TEXT
from src.Saliva.SalivaBase import SalivaBase


class AskForFormat(SalivaBase):
    format_selector = pn.widgets.Select(
        options=["", "Wide Format", "Plate Format"],
        name="Format",
    )
    ready = param.Boolean(default=False)

    def __init__(self, **params):
        params["HEADER_TEXT"] = ASK_FOR_FORMAT_TEXT
        super().__init__(**params)
        self.update_step(1)
        self.update_text(ASK_FOR_FORMAT_TEXT)
        self.format_selector.link(self, callbacks={"value": self.format_changed})
        self._view = pn.Column(
            self.header,
            self.format_selector,
        )

    def format_changed(self, _, event):
        self.format = event.new
        self.ready = bool(event.new)

    def panel(self):
        return self._view
```

This class inherits from the SalivaBase class which is defined in the SalivaBase.py file. This class is responsible 
to save the different parameters necessary for the analysis of the data so that the classes of the different steps 
can be smaller and more readable. 

The step classes all have a constructor which is responsible for different things. It sets the HEADER_TEXT field 
which is used to display the text at the top of the page, and it sets the number of its step. Another important task 
of the constructor is to link the [panel widgets](https://panel.holoviz.org/api/panel.widgets.html) to the different
functions of the class. There are different ways to bind widgets to functions and values as illustrated 
[here](https://panel.holoviz.org/how_to/links/index.html). The most important one for this project is the 
[link function](https://panel.holoviz.org/how_to/links/links.html). With this function it is possible to bind values
to other values but also to bind a change in properties (such as the value of a widget) to a function. 
The first parameter of the link function defines the target of the link, this can be the object itself. The 
callbacks parameter sets which function is called if the corresponding property changes. In this example the function 
format_changed is called if the value of the format_selector widget changes. The link function is called in the constructor
in order to ensure that per widget there is only one link. The method which is called by the link function (in this
example format_changed) gets three parameters: the first is the object itself, the second one is the target (here also the object) 
and the third one is an Event Object (this has different fields, e.g. event.new = the new value; event.old = the old value).
The last important part of the constructor is the setting 
of the _view field. This field is responsible for the actual content of the step. In this example it is a column 
which contains the header and the format_selector widget. The panel() function returns this _view field and is automatically
called whenever the step is displayed. Each step class also has an output() function which is called whenever the 
user presses the next button. In most of the cases (such as in the AskForFormat class) this function is implemented
by the corresponding base class (here SalivaBase). This function looks like this:

```python
    @param.output(
        ("selected_device", param.String),
        ("selected_parameters", param.Dict),
        ("data", param.Dynamic),
    )
    def output(self):
        return (
            self.selected_device,
            self.selected_parameters,
            self.data,
        )
```

The decorator of this function ( @param.output ) defines the fields which are filled in the class of the next step and 
the type of the field. In this example the next step gets the values for the selected_device, selected_parameters and
the data. 

### How to add a new pipeline

After you have learned how to create a new pipeline and its steps the following part will explain how to add a new pipeline 
to the main page. The main page is defined in the main.py file. The main page is a panel object which contains a reference
to the app itself. So to add a new pipeline you have to create a new 
[GridBox element](https://panel.holoviz.org/reference/layouts/GridBox.html) like this:

```python
physBtn = pn.widgets.Button(
            name="Physiological Data",
            sizing_mode="stretch_width",
            align="end",
            button_type="primary",
        )
        physBtn.on_click(self.start_pipeline)
        physCard = pn.GridBox(
            pn.pane.SVG(
                self.pathToIcons + "Physiological.svg",
                align=("center"),
                sizing_mode="stretch_both",
                max_height=150,
                max_width=200,
                styles={"background": "whitesmoke"},
            ),
            pn.Spacer(height=45),
            physBtn,
            ncols=1,
            styles={"background": "whitesmoke", "align": "center"},
            width=250,
            height=250,
        )
```
So you just create the Button, then link the on_click event to the start_pipeline function and then create the GridBox 
element with a path to an .svg-File indicating the icon of the pipeline, a spacer and the button. The GridBox element
is then added to the signal selection part of the main page:

```python
        signalSelection = pn.GridBox(
            *[physCard, psychCard, questionnaireCard, salCard, sleepCard],
            ncols=3,
            nrows=2,
            max_width=1000,
            height=600,
        )
```

The last step in adding a new pipeline is to add it to the name_pipeline_dict Dictionary:


```python
    name_pipeline_dict = {
        "Physiological Data": PhysiologicalPipeline(),
        "Psychological Data": PsychologicalPipeline(),
        "Questionnaire Data": QuestionnairePipeline(),
        "Saliva Data": SalivaPipeline(),
        "Sleep Data": SleepPipeline(),
    }
```

Here the key is the text on the Button you added above to the GridBox and the value is the pipeline object you created.
After that the new pipeline should be accessible in the main page. To also add the pipeline to the sidebar, you also 
have to add a Button to the sidebar and link the on_click event to the start_pipeline function. The following is an 
example for the Saliva pipeline:

```python
        salBtn = pn.widgets.Button(name="Saliva Data")
        salBtn.on_click(self.start_pipeline)
        column = pn.Column(
            homeBtn, physBtn, psychBtn, questionnaireBtn, salBtn, sleepBtn
        )
```

Congratulations, you should now know everything to create and add a new pipeline to the project.

## Contents of tests

The tests folder contains all the tests for the different pipelines. The tests are written with the pytest framework.
For the different pipelines there are different example files which are used for the tests. These files are located in
the test_data folder. The Tests for the pipelines are located in the corresponding pipeline folder. In these pipeline
folders there are different test files for the different steps of the pipeline for some steps are no tests, since they 
are just info pages. 
The tests for the different steps are written in the following way, the following is an example for the AskForFormat step:

```python
class TestAskForFormat:
    @pytest.fixture
    def ask_for_format(self):
        return AskForFormat()

    def test_ask_for_format(self, ask_for_format):
        assert ask_for_format is not None
        assert ask_for_format.ready == False
        possible_formats = ask_for_format.format_selector.options
        assert possible_formats == ["", "Wide Format", "Plate Format"]

    def test_ask_for_format_plate(self, ask_for_format):
        ask_for_format.format_selector.value = "Plate Format"
        assert ask_for_format.ready == True
        assert ask_for_format.format == "Plate Format"
        ask_for_format.format_selector.value = ""
        assert ask_for_format.ready == False
        assert ask_for_format.format == ""
        ask_for_format.format_selector.value = "Wide Format"
        assert ask_for_format.ready == True
        assert ask_for_format.format == "Wide Format"
```

The first function is a fixture which returns an instance of the AskForFormat class which can be used as an argument for
the other functions (so you don't have to manually create a new instance for each test). The second function is a test
function. The functions associated with a widget get called automatically if the value of the widget changes. So in this
case the format_changed function in the AskForFormat class gets called automatically if the value of the format_selector
widget changes.

For further information about the pytest framework you can take a look at the documentation of [pytest](https://pytest.org).

To run the tests locally you can use the following command:

```bash
poetry run poe test
```

You can also run the tests in the GitHub Actions workflow. The workflow is defined in the .github/workflows folder and
the tests are run on every push to the development branch and only if the tests are successful a new version of 
the project is deployed to the Github Pages.

## How to build the project


### Run the project locally without converting the files

You can either run the project locally via your IDE for that you just start the main function in the main_ide.py file.
Or you can use the following command:

```bash
poetry run poe run_local
```

With that command the project is started on the localhost and reloads automatically if you change something in the code 
and save it.


### Run the project locally as a standalone page

For that you have to run the following command:

```bash
poetry run poe build_pipelines
```

This command converts the porject into a Progressive Web App (PWA) and saves it in the index folder. In this folder you 
find the index.html file which is the standalone page, that uses the index.js File for the Javascript Code. 
You can open this file in your browser and use the project as a PWA. You can also deploy this file to a webserver, this 
is done automatically in a GitHub Actions workflow. The workflow is defined in the .github/workflows folder in the 
test_build_and_deploy.yml file. The workflow is triggered on every push to the development branch and only if the tests
are successful the project is deployed to the Github Pages.

The heart of the conversion is the convert_files.py file. This file has different tasks:

<ol>
    <li>It combines all the necessary .py Files into one large .py File</li>
    <li>Redundant Imports are removed from this index.py File</li>
    <li>It replaces all occurrences of the pn.state.notifications with app.notifications</li>
    <li>Converting the index.py File into a PWA using the [panel convert command](https://panel.holoviz.org/how_to/wasm/convert.html)</li>
    <li>Replacing the imports in the index.js File (to make it work as a standalone page)</li>
</ol>

You can also run the convert_files.py file directly with the following command:

```bash
poetry run poe convert_files
```

This command line interface then takes you through the different steps of the conversion process.

