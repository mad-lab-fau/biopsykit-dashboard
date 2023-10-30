from src import (
    MainPage,
    Physiological,
    Psychological,
    Questionnaire,
    Saliva,
    Sleep,
    utils,
)

__all__ = [
    "MainPage",
    "Physiological",
    "Psychological",
    "Questionnaire",
    "Saliva",
    "Sleep",
    "utils",
]

__version__ = "0.1.0"


def version() -> None:
    """Prints the version of BioPsyKit and its dependencies."""
    import os

    os.environ["OUTDATED_IGNORE"] = "1"
    import biopsykit as bp
    import param
    import panel as pn
    import pandas as pd
    from io import BytesIO
    from pathlib import Path
    from zipfile import ZipFile
    import nilspodlib
    import numpy as np
    import typing
    from packaging.version import Version
    from typing_extensions import Self
    import warnings
    import datetime as datetime
    from io import StringIO
    from panel.viewable import Viewer
    import io
    import zipfile
    import seaborn as sns
    import fau_colors
    from biopsykit.protocols import CFT
    from fau_colors import cmaps
    from matplotlib import pyplot as plt
    import re
    import string
    import pytz
    import plotly.express as px
    import matplotlib.pyplot as plt

    #
    # print(
    #     f"Operating System: {platform.system()} ({platform.architecture()[1]} {platform.architecture()[0]})\n",
    #     f"- Python: {platform.python_version()}\n",
    #     f"- BioPsyKit: {__version__}\n\n",
    #     f"- NumPy: {np.__version__}\n",
    #     f"- Pandas: {pd.__version__}\n",
    #     f"- SciPy: {scipy.__version__}\n",
    #     f"- matplotlib: {matplotlib.__version__}\n",
    #     f"- NeuroKit2: {neurokit2.__version__}\n",
    #     f"- pingouin: {pingouin.__version__}\n",
    # )
