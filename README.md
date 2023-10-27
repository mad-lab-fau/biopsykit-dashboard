# BioPsyKit Dashboard

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/mad-lab-fau/biopsykit-dashboard)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Test](https://github.com/mad-lab-fau/biopsykit-dashboard/actions/workflows/test.yml/badge.svg)](https://github.com/mad-lab-fau/biopsykit-dashboard/actions/workflows/test.yml)

## Table of contents
* [General info](#general-info)
* [Setup](#setup)
* [Convert to pyodide](#convert-to-pyodide)


## General info
This project is a Dashboard version of the BioPsyKit Python package. This enables researchers
to use this package without programming themselves but perform their analyses in the browser 
instead of a Python IDE. 
	


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
poetry run poe run_local
```

after that the Dashboard should start in your default Browser.

## Convert to pyodide
You can also convert the application to a pyodide application. This will create a single html file that can be opened in any browser. 
To do so, run the following command:

```bash
poetry run python convert_files.py
```

There you will be asked if you want to convert all the pipelines into one large app. However if you choose to do this
the resulting file will be too large to be run in the browser. Therefore you should choose to convert the pipelines 
individually. You can do this pipeline by pipeline. 


