import matplotlib
from fau_colors import cmaps


def make_pretty(styler):
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "", cmaps.faculties_light
    )
    styler.background_gradient(axis=None, vmin=1, vmax=5, cmap=cmap)
    return styler
