## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [TODO](#TODO)

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
poetry run Main.py
```

after that the Dashboard should start in your default Browser.

## TODO

* Two paths: 
  * Single Session
  * Multi Session
* Click on previous, the sampling rate Box has to be updated in order to proceed again
* In the Processing Step: Check Lower and upper Bound dynamically
* Stages: Select Subtypes, Results
* Adapted Nilspodlib: Change such that the porcessing is similar to read_csv in pandas and make a pull request
* Refactoring: Tests, Catch Exceptions, For each Stage a single Python File, etc.