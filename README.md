# BioPsyKit Dashboard

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/mad-lab-fau/biopsykit-dashboard)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)


## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [TODO](#TODO)
* [Questions](#questions)
## General info
This project is a Dashboard version of the BioPsyKit Python package. This enables researchers
to use this package without programming themselves but perform their analyses in the browser 
instead of a Python IDE. 
	
## Technologies
Project is created with:
* Python version: 3.10
* Panel: 0.14.2
* nilspodlib: 3.6.0
* biopsykit: 0.7.1
* pandas: 1.5.2
* numpy: 1.23.5
* typing-extensions: 4.4.0
* packaging: 21.3
* param: 1.12.2
* pytz: 2022.6
* holoviews: 1.15.2

	
## Setup
Install Python 3.10 and [poetry](https://python-poetry.org).
Then run the commands below to get the latest source and install the dependencies:

```bash
git clone https://github.com/mad-lab-fau/biopsykit-dashboard.git
cd biopsykit-dashboard
poetry install
```

To then run the Dashboard locally in your Browser:

```bash
poetry run python __main__.py
```

after that the Dashboard should start in your default Browser.

## TODO

- [X] Click on previous, the sampling rate Box has to be updated in order to proceed again
- [X] In the Processing Step: Check Lower and upper Bound dynamically
- [X] Stages: 
  - [X] Select Subtypes
  - [X] Results
- [X] Adapted Nilspodlib: Change such that the processing is similar to read_csv in pandas and make a pull request
- [ ] Refactoring: 
  - [ ] Tests
  - [ ] Catch Exceptions
  - [X] For each Stage a single Python File
  - [X] Progress Bar
- [X] Test ob App in WebAssembly konvertiert werden kann
  - [ ] Automatisieren, dass alle .py und .md Datei in eine Datei geladen wird
- 
## Questions
* Müssen multi sessions synced sein?
* load_synced_session müsste noch so angepasst werden, dass es auch eine Liste an Datasets annehmen kann
* Phasen sollte man auch noch selbst angeben können?
* Als vorletzte Phase soll der User noch angeben können welche Subtypen ausgewertet werden sollen, sind hiermit die Phasen gemeint?
* Bei biopsykit.io.nilspod.load_dataset_nilspod: hier kann man noch die Datastreams bekommen (so kann man später sagen, was alles zur Verfügung steht: ECG,
ACC: IMU; RSP: aus ECG Daten)
* 
