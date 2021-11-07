# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 20:56:13 2021

@author: Matthew Rowles
"""

import PySimpleGUI as sg
from pdCIFplotter import parse_cif as pc
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.colors as mc  # a lot of colour choices in here to use
# from timeit import default_timer as timer  # use as start = timer() ...  end = timer()
import mplcursors


DEBUG = True

def check_packages():
    psg = sg.__version__.split(".")
    msg = ""
    psgupgrade = "I think your PySimpleGUI is out of date.\nPlease run\n > python -m PySimpleGUI.PySimpleGUI upgrade\nto install the latest version from github."

    print(f"{psg=}")

    if int(psg[0]) <= 3:
        msg += psgupgrade
    if int(psg[1]) <= 52:
        msg += psgupgrade
    if int(psg[2]) <= 0 and len(psg) != 4:
        msg += psgupgrade

    if msg != "":
        msg += "\n\nI don't think it will break anything. You just won't get the full feature set."

    return msg


# Potential themes that work for me.
MY_THEMES = ["Default1", "GrayGrayGray", "Reddit", "SystemDefault1", "SystemDefaultForReal"]
sg.theme(MY_THEMES[2])
sg.set_options(dpi_awareness=True)

# global parameters
action_column_width = 30
canvas_x = 600
canvas_y = 300

single_fig = None
single_ax = None
single_figure_agg = None
y_style = \
    [
        ["mediumblue", "+", "none", "2"],  # yobs
        ["red", None, "solid", "1"],  # ycalc
        ["gray", None, "solid", "2"],  # ybkg
        ["lightgrey", None, "solid", "2"],  # ydiff
        ["lightgrey", None, "solid", "1"]  # cRwp
    ]

stack_fig = None
stack_ax = None
stack_figure_agg = None

surface_fig = None
surface_ax = None
surface_figure_agg = None
surface_z_color = "viridis"
surface_plot_data = {"x_ordinate": "", "y_ordinate": "", "z_ordinate": "",
                     "x_data": None, "y_data": None, "z_data": None, "plot_list": []}

cif = {}  # the cif dictionary from my parsing
single_data_list = []  # a list of all pattern blocknames in the cif
single_dropdown_lists = {}  # all of the appropriate x and y ordinates for each pattern

stack_x_ordinates = []
stack_y_ordinates = {}

surface_x_ordinates = []
surface_z_ordinates = {}


def debug(*args):
    if DEBUG:
        print(*args)

def reset_globals():
    """
    Resets all the contents of global parameters of interest.
    Takes them back to empty lists, dictionarys, or None, as appropriate
    Initialising them again is somebody else's problem...
    :return:
    """
    global single_fig, single_ax, single_figure_agg
    global stack_fig, stack_ax, stack_figure_agg
    global surface_fig, surface_ax, surface_figure_agg

    global cif
    global single_data_list, single_dropdown_lists
    global stack_x_ordinates, stack_y_ordinates
    global surface_x_ordinates, surface_z_ordinates, surface_plot_data

    single_fig = None
    single_ax = None
    single_figure_agg = None

    stack_fig = None
    stack_ax = None
    stack_figure_agg = None

    surface_fig = None
    surface_ax = None
    surface_figure_agg = None
    surface_plot_data = {"x_ordinate": None, "y_ordinate": None, "z_ordinate": None,
                         "x_data": None, "y_data": None, "z_data": None, "plot_list": None}

    cif = {}  # the cif dictionary from my parsing
    single_data_list = []  # a list of all pattern blocknames in the cif
    single_dropdown_lists = {}  # all of the appropriate x and y ordinates for each pattern

    stack_x_ordinates = []
    stack_y_ordinates = {}

    surface_x_ordinates = []
    surface_z_ordinates = {}


# LINE_MARKER_COLORS = list(mc.CSS4_COLORS.keys())
# from here: https://matplotlib.org/stable/gallery/color/named_colors.html
_by_hsv = sorted((tuple(mc.rgb_to_hsv(mc.to_rgb(color))), name) for name, color in mc.CSS4_COLORS.items())
LINE_MARKER_COLORS = [name for hsv, name in _by_hsv]
MARKER_STYLES = [None, ".", "o", "s", "*", "+", "x", "D"]
LINE_STYLES = ["solid", "None", "dashed", "dashdot", "dotted"]
LINE_MARKER_SIZE = [str(s) for s in range(1, 10)]

SURFACE_COLOR_MAPS_SOURCE = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

SURFACE_COLOR_MAPS = []
for c in SURFACE_COLOR_MAPS_SOURCE:
    SURFACE_COLOR_MAPS.append(c)
    SURFACE_COLOR_MAPS.append(c + "_r")

# these lists contain all the possible x and y ordinate data items that I want to worry about in this program
# the last few entries in each list correspond to values that could potentially be calc'd from the given
# information, but were not presented in the CIF.
COMPLETE_X_LIST = pc.ParseCIF.COMPLETE_X_LIST
OBSERVED_Y_LIST = pc.ParseCIF.OBSERVED_Y_LIST
CALCULATED_Y_LIST = pc.ParseCIF.CALCULATED_Y_LIST
BACKGROUND_Y_LIST = pc.ParseCIF.BACKGROUND_Y_LIST
COMPLETE_XY_PLAINTEXT_DICT = {"_pd_meas_2theta_scan": "\u00B0 2\u03b8 measured",
                              "_pd_proc_2theta_corrected": "\u00B0 2\u03b8 corrected",
                              "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                              "_pd_meas_position": "Position (mm)",
                              "_pd_proc_energy_incident": "Incident energy (eV)",
                              "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                              "_pd_proc_d_spacing": "d spacing (\u212b)",
                              "_pd_proc_recip_len_Q": "q (1/\u212b)",
                              "d": "d spacing (calc'd from 2\u03b8) (\u212b)",
                              "q": "q (calc'd from 2\u03b8) (1/\u212b)",
                              "_pd_meas_counts_total": "Total measured counts",
                              "_pd_meas_intensity_total": "Total measured intensity",
                              "_pd_proc_intensity_total": "Total processed intensity",
                              "_pd_proc_intensity_net": "Net processed intensity",
                              "_pd_calc_intensity_net": "Net calculated intensity",
                              "_pd_calc_intensity_total": "Total calculated intensity",
                              "_pd_meas_counts_background": "Background measured counts",
                              "_pd_meas_counts_container": "Container measured counts",
                              "_pd_meas_intensity_background": "Background measured intensity",
                              "_pd_meas_intensity_container": "Container measured intensity",
                              "_pd_proc_intensity_bkg_calc": "Calculated background intensity",
                              "_pd_proc_intensity_bkg_fix": "Background intensity, fixed points",
                              "diff": "Difference"}


def pretty(d, indent=0, print_values=True):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1, print_values=print_values)
        else:
            if print_values:
                print('\t' * (indent + 1) + str(value))


def single_update_plot(pattern, x_ordinate, y_ordinates: list,
                       plot_hkls: bool, plot_diff: bool, plot_cchi2: bool,
                       axis_scale: dict, window):
    global single_figure_agg, single_fig, single_ax

    dpi = plt.gcf().get_dpi()
    if single_fig is not None:
        single_height_px = single_fig.get_size_inches()[1] * dpi
    else:
        single_height_px = 382

    # if single_fig is None or single_ax is None:
    if single_fig is not None:
        plt.close(single_fig)
    single_fig, single_ax = plt.subplots(1, 1)
    single_fig = plt.gcf()
    single_fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    single_fig.set_tight_layout(True)
    plt.margins(x=0)

    cifpat = cif[pattern]

    x = cifpat[x_ordinate]
    if axis_scale["x"] == "log":
        x = np.log10(x)
    elif axis_scale["x"] == "sqrt":
        x = np.sqrt(x)

    ys = []
    for y in y_ordinates:
        if y != "None":
            tmp_y = cifpat[y]
            if axis_scale["y"] == "log":
                tmp_y = np.log10(tmp_y)
            elif axis_scale["y"] == "sqrt":
                tmp_y = np.sqrt(tmp_y)
            ys.append(tmp_y)
        else:
            ys.append(None)

    # need to calculate diff after the y axis transforms to get the right magnitudes
    if plot_diff:
        ydiff = ys[0] - ys[1]
        ys.append(ydiff)
        y_ordinates.append("Diff")
    else:
        ys.append(None)
        y_ordinates.append("Diff")

    min_plot = 999999999
    max_plot = -min_plot
    cchi2_zero = 0
    for i, (y, y_name) in enumerate(zip(ys, y_ordinates)):
        if y is not None:
            if y_name == "Diff":
                offset = min_plot - np.nanmax(y)
                y += offset
                plt.plot(x, [offset] * len(x), color="black", marker=None, linestyle=(0, (5, 10)), linewidth=1)  # "loosely dashed"

            plt.plot(x, y, label=" " + y_name,
                     color=y_style[i][0], marker=y_style[i][1],
                     linestyle=y_style[i][2], linewidth=y_style[i][3],
                     markersize=float(y_style[i][3]) * 3
                     )
            # keep track of min and max to plot hkl ticks and diff correctly
            min_plot = min(min_plot, min(y))
            max_plot = max(max_plot, max(y))
            if y_name != "Diff":
                cchi2_zero = min_plot

    # hkl plotting below     single_height_px
    hkl_x_ordinate_mapping = {"_pd_proc_d_spacing": "_refln_d_spacing", "d": "_refln_d_spacing", "q": "refln_q", "_pd_meas_2theta_scan": "refln_2theta",
                              "_pd_proc_2theta_corrected": "refln_2theta"}
    single_hovertexts=[]
    single_hkl_artists=[]
    if plot_hkls:
        y_range = max_plot - min_plot
        hkl_markersize_pt = 6
        hkl_markersize_px = hkl_markersize_pt * 72 / dpi
        num_hkl_rows = len(cifpat["str"].keys())
        hkl_tick_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows

        hkl_x_ordinate = hkl_x_ordinate_mapping[x_ordinate]
        for i, phase in enumerate(cifpat["str"].keys()):
            hkl_x = cifpat["str"][phase][hkl_x_ordinate]
            hkl_y = [min_plot - 4 * (i + 1) * hkl_tick_spacing] * len(hkl_x)

            if axis_scale["x"] == "log":
                hkl_x = np.log10(hkl_x)
            elif axis_scale["x"] == "sqrt":
                hkl_x = np.sqrt(hkl_x)

            hkl_tick, = single_ax.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt)
            single_hkl_artists.append(hkl_tick)
            if "refln_hovertext" in cifpat["str"][phase]:
                single_hovertexts.append(cifpat["str"][phase]["refln_hovertext"])
            else:
                single_hovertexts.append([phase]*len(hkl_x))

        # https://stackoverflow.com/a/58350037/36061
        single_hkl_hover_dict = dict(zip(single_hkl_artists, single_hovertexts))
        mplcursors.cursor(single_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
            "add", lambda sel: sel.annotation.set_text(single_hkl_hover_dict[sel.artist][sel.index]))
    #end hkl if

    if plot_cchi2:
        # https://stackoverflow.com/a/10482477/36061
        def align_cchi2(ax1, v1, ax2):
            """adjust cchi2 ylimits so that 0 in cchi2 axis is aligned to v1 in main axis"""
            miny1, maxy1 = ax1.get_ylim()
            rangey1 = maxy1 - miny1
            f = (v1 - miny1) / rangey1
            _, maxy2 = ax2.get_ylim()
            miny2 = (f / (f - 1)) * maxy2
            ax2.set_ylim(miny2, maxy2)

        cchi2 = pc.calc_cumchi2(cifpat, y_ordinates[0], y_ordinates[1])
        if axis_scale["y"] == "log":
            cchi2 = np.log10(cchi2)
        elif axis_scale["y"] == "sqrt":
            cchi2 = np.sqrt(cchi2)
        single_ax2 = single_ax.twinx()
        single_ax2.plot(x, cchi2, label=" c\u03C7\u00b2",
                        color=y_style[4][0], marker=y_style[4][1],
                        linestyle=y_style[4][2], linewidth=y_style[4][3],
                        markersize=float(y_style[3][3]) * 3
                        )
        single_ax2.set_yticklabels([])
        single_ax2.set_yticks([])
        single_ax2.margins(x=0)
        single_ax2.set_ylabel("c\u03C7\u00b2")
        align_cchi2(single_ax, cchi2_zero, single_ax2)

        # organise legends:
        # https://stackoverflow.com/a/10129461/36061
        # ask matplotlib for the plotted objects and their labels
        lines, labels = single_ax.get_legend_handles_labels()
        lines2, labels2 = single_ax2.get_legend_handles_labels()
        single_ax2.legend(lines + lines2, labels + labels2, loc='upper right', frameon=False)

    if not plot_cchi2:
        plt.legend(frameon=False, loc='upper right')  # loc='best')

    if "intensity" in y_ordinates[0]:
        y_axis_title = "Intensity (arb. units)"
    else:
        y_axis_title = "Counts"

    wavelength = pc.get_from_cif(cifpat, "wavelength")
    if axis_scale["x"] == "log":
        x_axis_label = f"Log10[{x_axis_title(x_ordinate, wavelength)}]"
    elif axis_scale["x"] == "sqrt":
        x_axis_label = f"Sqrt[{x_axis_title(x_ordinate, wavelength)}]"
    else:
        x_axis_label = f"{x_axis_title(x_ordinate, wavelength)}"

    if axis_scale["y"] == "log":
        y_axis_title = f"Log10[{y_axis_title}]"
    elif axis_scale["y"] == "sqrt":
        y_axis_title = f"Sqrt[{y_axis_title}]"

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()

    single_ax.set_xlabel(x_axis_label)
    single_ax.set_ylabel(y_axis_title)
    plt.title(pattern, loc="left")

    # https://stackoverflow.com/a/30506077/36061
    if plot_cchi2:
        single_ax.set_zorder(single_ax2.get_zorder() + 1)
        single_ax.patch.set_visible(False)

    single_figure_agg = draw_figure_w_toolbar(window["single_plot"].TKCanvas, single_fig,
                                              window["single_matplotlib_controls"].TKCanvas)


def stack_update_plot(x_ordinate, y_ordinate, offset, plot_hkls: bool, axis_scale: dict, window):
    global stack_figure_agg, stack_fig, stack_ax

    debug(f"stack {x_ordinate=}")
    debug(f"stack {y_ordinate=}")
    debug(f"stack {offset=}")
    debug(f"stack {axis_scale=}")

    dpi = plt.gcf().get_dpi()
    if stack_fig is not None:
        stack_height_px = stack_fig.get_size_inches()[1] * dpi
    else:
        stack_height_px = 382

    if stack_fig is not None:
        plt.close(stack_fig)
    stack_fig, stack_ax = plt.subplots(1, 1)
    stack_fig = plt.gcf()
    dpi = stack_fig.get_dpi()
    stack_fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    stack_fig.set_tight_layout(True)
    plt.margins(x=0)

    # generate a list of patterns that validly match the chosen x and y ordinates
    plot_list = []
    for pattern in cif.keys():
        cifpat = cif[pattern]
        if x_ordinate in cifpat and y_ordinate in cifpat:
            debug(f"I can legally plot {pattern}")
            plot_list.append(pattern)

    debug("before scale")
    debug(f"{offset=}")
    # compile all of the patterns' data
    if axis_scale["y"] == "log":
        offset = np.log10(offset)
    elif axis_scale["y"] == "sqrt":
        offset = np.sqrt(offset)
    # need to loop backwards so that the data comes out in the correct order for plotting
    for i in range(len(plot_list) - 1, -1, -1):
        pattern = plot_list[i]
        debug(f"Now plotting {pattern}")
        cifpat = cif[pattern]
        x = cifpat[x_ordinate]
        y = cifpat[y_ordinate]
        label = pattern
        debug("before scale")
        debug(f"{x=}")
        debug(f"{y=}")
        if axis_scale["x"] == "log":
            x = np.log10(x)
        elif axis_scale["x"] == "sqrt":
            x = np.sqrt(x)
        if axis_scale["y"] == "log":
            y = np.log10(y)
        elif axis_scale["y"] == "sqrt":
            y = np.sqrt(y)
        debug("after scale")
        debug(f"{x=}")
        debug(f"{y=}")

        plt.plot(x, y + i * offset, label=label)  # do I want to fill white behind each plot?

    # https://mplcursors.readthedocs.io/en/stable/examples/artist_labels.html
    stack_artists = stack_ax.get_children()
    mplcursors.cursor(stack_artists, hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))

    if "intensity" in y_ordinate:
        y_axis_title = "Intensity (arb. units)"
    else:
        y_axis_title = "Counts"

    # check that the wavelength for all patterns is the same
    wavelength = pc.get_from_cif(cif[plot_list[0]], "wavelength")
    for pattern in plot_list:
        if wavelength != pc.get_from_cif(cif[pattern], "wavelength"):
            wavelength = None
            break

    if axis_scale["x"] == "log":
        x_axis_label = f"Log10[{x_axis_title(x_ordinate, wavelength)}]"
    elif axis_scale["x"] == "sqrt":
        x_axis_label = f"Sqrt[{x_axis_title(x_ordinate, wavelength)}]"
    else:
        x_axis_label = f"{x_axis_title(x_ordinate, wavelength)}"

    if axis_scale["y"] == "log":
        y_axis_title = f"Log10[{y_axis_title}]"
    elif axis_scale["y"] == "sqrt":
        y_axis_title = f"Sqrt[{y_axis_title}]"

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()

    stack_ax.set_xlabel(x_axis_label)
    stack_ax.set_ylabel(y_axis_title)

    stack_figure_agg = draw_figure_w_toolbar(window["stack_plot"].TKCanvas, stack_fig,
                                             window["stack_matplotlib_controls"].TKCanvas)


def surface_update_plot(x_ordinate, z_ordinate, plot_hkls: bool, axis_scale: dict, window):
    global surface_figure_agg, surface_fig, surface_ax, surface_z_color, surface_plot_data
    y_ordinate = "Pattern number"

    dpi = plt.gcf().get_dpi()

    if surface_fig is not None:
        plt.close(surface_fig)
    surface_fig, surface_ax = plt.subplots(1, 1)
    surface_fig = plt.gcf()
    surface_fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    surface_fig.set_tight_layout(True)
    plt.margins(x=0)

    # am I plotting the data I already have? If all the ordinates are the same, then I don't need to regrab all of the data
    #  and I can just use what I already have.
    if surface_plot_data["x_ordinate"] == x_ordinate and \
            surface_plot_data["y_ordinate"] == y_ordinate and \
            surface_plot_data["z_ordinate"] == z_ordinate:
        debug("reusing surface plot data")
        xx = surface_plot_data["x_data"]
        yy = surface_plot_data["y_data"]
        zz = surface_plot_data["z_data"]
        plot_list = surface_plot_data["plot_list"]
    else:
        # need to construct a single array for each x, y, z, by looping through only those patterns which have the
        # x and z ordinates necessary to make the piccie I want to see.
        debug("Constructing surface plot data")
        xs = []
        ys = []
        zs = []
        i = 1
        plot_list = []
        min_x = 9999999999
        max_x = -min_x
        x_step = 0
        # get all of the original data
        for pattern in cif.keys():
            cifpat = cif[pattern]
            if not (x_ordinate in cif[pattern] and z_ordinate in cif[pattern]):
                continue
            # we now know that both x and z are in the pattern
            plot_list.append(pattern)

            x = cifpat[x_ordinate]
            z = cifpat[z_ordinate]

            debug("---")
            debug(pattern)
            debug("before flip")
            debug(f"{x=}")
            debug(f"{z=}")

            if x[0] > x[-1]:  # ie if x is decreasing
                x = np.flip(x)
                z = np.flip(z)

            debug("after flip")
            debug(f"{x=}")
            debug(f"{z=}")

            min_x = min(min_x, min(x))
            max_x = max(max_x, max(x))
            x_step += np.average(np.diff(x))

            debug(f"{min_x=}")
            debug(f"{max_x=}")
            debug(f"{x_step/i}")

            xs.append(x)
            zs.append(z)
            ys.append(i)
            i += 1
        else:
            x_step /= i

        # create the x interpolation array
        xi = np.arange(min_x, max_x, math.fabs(x_step))
        # interpolate each diffraction pattern
        for j in range(len(xs)):
            zs[j] = np.interp(xi, xs[j], zs[j], left=float("nan"), right=float("nan"))

        # https://stackoverflow.com/a/33943276/36061
        # https://stackoverflow.com/a/38025451/36061
        xx, yy = np.meshgrid(xi, ys)
        # zz = z.reshape(len(y), len(x))
        zz = np.array(zs)

        # update the surface_plot_data information, so I don't need to do those recalculations everytime if I don't have to.
        surface_plot_data["x_ordinate"] = x_ordinate
        surface_plot_data["y_ordinate"] = y_ordinate
        surface_plot_data["z_ordinate"] = z_ordinate
        surface_plot_data["x_data"] = xx
        surface_plot_data["y_data"] = yy
        surface_plot_data["z_data"] = zz
        surface_plot_data["plot_list"] = plot_list
    # end of if

    debug("scaling surface plot data")
    if axis_scale["x"] == "log":
        xx = np.log10(xx)
    elif axis_scale["x"] == "sqrt":
        xx = np.sqrt(xx)
    if axis_scale["y"] == "log":
        yy = np.log10(yy)
    elif axis_scale["y"] == "sqrt":
        yy = np.sqrt(yy)
    if axis_scale["z"] == "log":
        zz = np.log10(zz)
    elif axis_scale["z"] == "sqrt":
        zz = np.sqrt(zz)

    debug("plotting surface plot")
    print(f"{xx=}")
    print(f"{yy=}")
    print(f"{zz=}")
    plt.pcolormesh(xx, yy, zz, shading='nearest', cmap=surface_z_color)

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()


    # hkl plotting below     single_height_px
    hkl_x_ordinate_mapping = {"_pd_proc_d_spacing": "_refln_d_spacing", "d": "_refln_d_spacing", "q": "refln_q", "_pd_meas_2theta_scan": "refln_2theta",
                              "_pd_proc_2theta_corrected": "refln_2theta"}
    surface_hovertexts=[]
    surface_hkl_artists=[]
    if plot_hkls:
        debug("plotting hkls")
        # y_range = max_plot - min_plot
        hkl_markersize_pt = 6
        # hkl_markersize_px = hkl_markersize_pt * 72 / dpi
        # num_hkl_rows = len(cifpat["str"].keys())
        # hkl_tick_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows

        hkl_x_ordinate = hkl_x_ordinate_mapping[x_ordinate]
        for pattern, ys in zip(plot_list, yy):
            cifpat = cif[pattern]
            y = ys[0]
            for i, phase in enumerate(cifpat["str"].keys()):
                debug(f"Should be plotting hkls for {phase}, which is number {i}.")

                hkl_x = cifpat["str"][phase][hkl_x_ordinate]
                hkl_y = [y] * len(hkl_x)

                if axis_scale["x"] == "log":
                    hkl_x = np.log10(hkl_x)
                elif axis_scale["x"] == "sqrt":
                    hkl_x = np.sqrt(hkl_x)
                if axis_scale["y"] == "log":
                    hkl_y = np.log10(hkl_y)
                elif axis_scale["y"] == "sqrt":
                    hkl_y = np.sqrt(hkl_y)

                colours = mc.TABLEAU_COLORS
                values = list(colours.values())
                num_values = len(values)
                idx = i % num_values

                hkl_tick, = surface_ax.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt, color=values[idx])
                surface_hkl_artists.append(hkl_tick)
                if "refln_hovertext" in cifpat["str"][phase]:
                    hovertext = [f"{phase}: {hkls}" for hkls in cifpat["str"][phase]["refln_hovertext"]]
                    surface_hovertexts.append(hovertext)
                else:
                    surface_hovertexts.append([phase]*len(hkl_x))

        # https://stackoverflow.com/a/58350037/36061
        surface_hkl_hover_dict = dict(zip(surface_hkl_artists, surface_hovertexts))
        mplcursors.cursor(surface_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
            "add", lambda sel: sel.annotation.set_text(surface_hkl_hover_dict[sel.artist][sel.index]))
    #end hkl if

    debug("Setting surface plot axis labels")
    # check that the wavelength for all patterns is the same
    wavelength = pc.get_from_cif(cif[plot_list[0]], "wavelength")
    for pattern in plot_list:
        if wavelength != pc.get_from_cif(cif[pattern], "wavelength"):
            wavelength = None
            break

    y_axis_title = "Pattern number"
    z_axis_title = z_ordinate
    if axis_scale["x"] == "log":
        x_axis_label = f"Log10[{x_axis_title(x_ordinate, wavelength)}]"
    elif axis_scale["x"] == "sqrt":
        x_axis_label = f"Sqrt[{x_axis_title(x_ordinate, wavelength)}]"
    else:
        x_axis_label = f"{x_axis_title(x_ordinate, wavelength)}"

    if axis_scale["y"] == "log":
        y_axis_title = f"Log10[{y_axis_title}]"
    elif axis_scale["y"] == "sqrt":
        y_axis_title = f"Sqrt[{y_axis_title}]"

    if axis_scale["z"] == "log":
        z_axis_title = f"Log10[{z_axis_title}]"
    elif axis_scale["z"] == "sqrt":
        z_axis_title = f"Sqrt[{z_axis_title}]"

    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_title)
    plt.colorbar(label=z_axis_title)

    debug("About to set the agg for the aurface plot")
    surface_figure_agg = draw_figure_w_toolbar(window["surface_plot"].TKCanvas, surface_fig,
                                               window["surface_matplotlib_controls"].TKCanvas)
    debug("Got to the end of the surface plot")


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
# https://github.com/PySimpleGUI/PySimpleGUI/issues/3989#issuecomment-794005240
def draw_figure_w_toolbar(canvas, figure, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(figure, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.update()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)


def y_ordinate_styling_popup(window_title, color_default, marker_styles_default, line_style_default, size_default, key, window):
    layout_def = \
        [
            [sg.Text(f"Here's the \nuser-defined \npopup for {key}!!!")],
            [sg.Combo(LINE_MARKER_COLORS, default_value=color_default, key=key + "-popup-color"),
             sg.Combo(MARKER_STYLES, default_value=marker_styles_default, key=key + "-popup-markerstyle"),
             sg.Combo(LINE_STYLES, default_value=line_style_default, key=key + "-popup-linestyle"),
             sg.Combo(LINE_MARKER_SIZE, default_value=size_default, key=key + "-popup-size")],
            [sg.Button("Ok", key=key + "-popup-ok", enable_events=True),
             sg.Button("Cancel", key=key + "-popup-cancel", enable_events=True)]
        ]
    win = sg.Window(window_title, layout_def, modal=True, grab_anywhere=True, enable_close_attempted_event=True)
    event, values = win.read()
    win.close()
    window.write_event_value(event, values)


def z_ordinate_styling_popup(window_title, color_default, key, window):
    layout_def = [
        [sg.Text(f"Here's the \nuser-defined \npopup for {key}!!!")],
        [sg.Combo(SURFACE_COLOR_MAPS, default_value=color_default, key=key + "-popup-color")],
        [sg.Button("Ok", key=key + "-popup-ok", enable_events=True),
         sg.Button("Cancel", key=key + "-popup-cancel", enable_events=True)]
    ]
    win = sg.Window(window_title, layout_def, modal=True, grab_anywhere=True, enable_close_attempted_event=True)
    event, values = win.read()
    win.close()
    window.write_event_value(event, values)


######################################################################################################
#######################################################################################################
######################################################################################################

def make_list_for_ordinate_dropdown(complete_list, possible_list, add_none=True):
    used_list = []
    for t in complete_list:
        if t in possible_list:
            used_list.append(t)
    if add_none:
        used_list.append("None")
    return used_list


def x_axis_title(x_ordinate, wavelength=None):
    if wavelength is None:
        wavelength = "(Wavelength unknown)"
    else:
        wavelength = f"(\u03BB = {wavelength} \u212b)"
    X_AXIS_TITLES = {"_pd_meas_2theta_scan": f"\u00B0 2\u03b8 {wavelength}",
                     "_pd_proc_2theta_corrected": f"\u00B0 2\u03b8 corrected {wavelength}",
                     "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                     "_pd_meas_position": "Position (mm)",
                     "_pd_proc_energy_incident": "Incident energy (eV)",
                     "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                     "_pd_proc_d_spacing": "d spacing (\u212b)",
                     "_pd_proc_recip_len_Q": "q (1/\u212b)",
                     "d": "d spacing (\u212b)",
                     "q": "q (1/\u212b)"}
    return X_AXIS_TITLES[x_ordinate]


def read_cif(filename):
    global cif
    cif = pc.ParseCIF(filename).get_processed_cif()


def make_xy_dropdown_list(master_list, difpat, add_none=True):
    return make_list_for_ordinate_dropdown(master_list, cif[difpat].keys(), add_none=add_none)


def initialise_pattern_and_dropdown_lists():
    global single_data_list, single_dropdown_lists
    single_data_list = [pattern for pattern in cif.keys()]
    for pattern in single_data_list:
        single_dropdown_lists[pattern] = {}
        # these are the possible values that the ordinate could be
        single_dropdown_lists[pattern]["x_values"] = make_xy_dropdown_list(COMPLETE_X_LIST, pattern, False)
        single_dropdown_lists[pattern]["yobs_values"] = make_xy_dropdown_list(OBSERVED_Y_LIST, pattern)
        single_dropdown_lists[pattern]["ycalc_values"] = make_xy_dropdown_list(CALCULATED_Y_LIST, pattern)
        single_dropdown_lists[pattern]["ybkg_values"] = make_xy_dropdown_list(BACKGROUND_Y_LIST, pattern)
        # this is my choice of the initial value of that ordinate
        single_dropdown_lists[pattern]["x_value"] = single_dropdown_lists[pattern]["x_values"][0]
        single_dropdown_lists[pattern]["yobs_value"] = single_dropdown_lists[pattern]["yobs_values"][0]
        single_dropdown_lists[pattern]["ycalc_value"] = single_dropdown_lists[pattern]["ycalc_values"][0]
        single_dropdown_lists[pattern]["ybkg_value"] = single_dropdown_lists[pattern]["ybkg_values"][0]


def initialise_stack_xy_lists():
    """
    Goes through every pattern and looks for an x-ordinate. If that x-ordinate isn't already in the list,
    add it to the list, and also add it as a potential pair with a y ordinate.
    Also check all the y-ordinates that match with a particular x-ordinate
    :return:
    """
    global stack_x_ordinates, stack_y_ordinates
    stack_x_ordinates = []
    stack_y_ordinates = {}
    for pattern in cif.keys():
        for x_ordinate in pc.ParseCIF.COMPLETE_X_LIST:
            if x_ordinate in cif[pattern]:
                if x_ordinate not in stack_x_ordinates:
                    stack_x_ordinates.append(x_ordinate)
                    stack_y_ordinates[x_ordinate] = []
                for y_ordinate in pc.ParseCIF.COMPLETE_Y_LIST:
                    if y_ordinate in cif[pattern] and y_ordinate not in stack_y_ordinates[x_ordinate]:
                        stack_y_ordinates[x_ordinate].append(y_ordinate)


def initialise_surface_xz_lists():
    """
    Goes through every pattern and looks for an x-ordinate. If that x-ordinate isn't already in the list,
    add it to the list, and also add it as a potential pair with a z ordinate.
    Also check all the z-ordinates that match with a particular z-ordinate
    :return:
    """
    global surface_x_ordinates, surface_z_ordinates
    surface_x_ordinates = []
    surface_z_ordinates = {}
    for pattern in cif.keys():
        for x_ordinate in pc.ParseCIF.COMPLETE_X_LIST:
            if x_ordinate in cif[pattern]:
                if x_ordinate not in surface_x_ordinates:
                    surface_x_ordinates.append(x_ordinate)
                    surface_z_ordinates[x_ordinate] = []
                for y_ordinate in pc.ParseCIF.COMPLETE_Y_LIST:
                    if y_ordinate in cif[pattern] and y_ordinate not in surface_z_ordinates[x_ordinate]:
                        surface_z_ordinates[x_ordinate].append(y_ordinate)


# single                                    # stack                                     # surface
# --------------------------------------- # # --------------------------------------- # # --------------------------------------- #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      | data_chooser | # # |                      | plot_control | # # |                      | plot_control | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      |--------------| # # |                      |              | # # |                      |              | #
# |                      | plot_control | # # |                      |              | # # |                      |              | #
# |         plot         |              | # # |         plot         |              | # # |         plot         |              | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |                      |              | # # |                      |              | # # |                      |              | #
# |-------------------------------------| # # |-------------------------------------| # # |-------------------------------------| #

decimalplaces = 4


def label_dropdown_row(label, values, default, key):
    return [sg.T(label),
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True, size=30)]


def label_dropdown_button_row(label, button_text, values, default, key):
    return [sg.T(label),
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True, size=30),
            sg.Button(button_text=button_text, key=key + "_button")]


def checkbox_button_row(checkbox_text, button_text, default, key):
    return [sg.Checkbox(checkbox_text, enable_events=True, default=default, key=key),
            sg.Stretch(),
            sg.Button(button_text=button_text, key=key + "_button")]


#################################################################################################################
#
# --- single tab
#
#################################################################################################################
single_keys = {"data": "single_data_chooser",  # this entry must remain at the beginning
               "x_axis": "single_x_ordinate",
               "yobs": "single_yobs_ordinate",
               "ycalc": "single_ycalc_ordinate",
               "ybkg": "single_ybkg_ordinate",
               "ydiff": "single_ydiff_checkbox",
               "hkl_checkbox": "single_hkl_checkbox",
               "hkl_above": "single_hkl_checkbox_above",
               "hkl_below": "single_hkl_checkbox_below",
               "cchi2": "single_cchi2_checkbox",
               "x_scale_linear": "single_x_scale_linear",
               "x_scale_sqrt": "single_x_scale_sqrt",
               "x_scale_log": "single_x_scale_log",
               "y_scale_linear": "single_y_scale_linear",
               "y_scale_sqrt": "single_y_scale_sqrt",
               "y_scale_log": "single_y_scale_log"}

single_keys_with_buttons = ["yobs", "ycalc", "ybkg", "ydiff", "cchi2"]
single_buttons_keys = {k: single_keys[k] + "_button" for k in single_keys_with_buttons}
single_buttons_values = {v: (k, i) for i, (k, v) in enumerate(single_buttons_keys.items())}


def update_single_element_disables(pattern, values, window):
    if pattern == "":
        return

    # enable all buttons and dropdowns
    for key in single_keys.keys():
        window[single_keys[key]].update(disabled=False)
    for key in single_buttons_keys.keys():
        window[single_buttons_keys[key]].update(disabled=False)

    # disable buttons and dropdowns that need disabling
    #   if y list is length 1 (ie it says "None") disable ycombo and button
    for yname in ["yobs", "ycalc", "ybkg"]:
        if len(single_dropdown_lists[pattern][yname + "_values"]) == 1:
            window[single_keys[yname]].update(disabled=True)
            window[single_buttons_keys[yname]].update(disabled=True)
    #   if yobs or ycalc lists are length 1, disable difference checkbox and cumRwp checbox
    #  or if you've chosen one of them to be none
    if (len(single_dropdown_lists[pattern]["yobs_values"]) == 1 or len(single_dropdown_lists[pattern]["ycalc_values"]) == 1) or \
            (values[single_keys["yobs"]] == "None" or values[single_keys["ycalc"]] == "None"):
        window[single_keys["ydiff"]].update(disabled=True, value=False)
        window[single_keys["cchi2"]].update(disabled=True, value=False)
    #   If there isn't at least one hkl list, or you've chosen an x-ordinate that
    #   doesn't allow hkl ticks, disable hkl checkbox and radio
    if "str" not in cif[pattern] or values[single_keys["x_axis"]] in ["_pd_meas_time_of_flight", "_pd_meas_position"]:
        window[single_keys["hkl_checkbox"]].update(disabled=True, value=False)
        window[single_keys["hkl_above"]].update(disabled=True)
        window[single_keys["hkl_below"]].update(disabled=True)


layout_single_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="single_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Sizer(v_pixels=60), sg.Canvas(key="single_matplotlib_controls")]
    ]

layout_single_data_chooser = \
    [[
        sg.Combo(values=["Load some files to start!"],
                 default_value="Load some files to start!",
                 # size=(action_column_width, 10),
                 enable_events=True,
                 key=single_keys["data"],
                 readonly=True),
        sg.Push(),
    ]]

layout_single_plot_control = \
    [
        label_dropdown_row("X axis:  ", [], "", single_keys["x_axis"]),
        label_dropdown_button_row("Y(obs): ", "Options", [], "", single_keys["yobs"]),
        label_dropdown_button_row("Y(calc):", "Options", [], "", single_keys["ycalc"]),
        label_dropdown_button_row("Y(bkg): ", "Options", [], "", single_keys["ybkg"]),
        # label_dropdown_button_row("Y axis 4:", "Options", y_list, "", "single_y4_ordinate"),
        checkbox_button_row("Show difference plot", "Options", False, single_keys["ydiff"]),
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key=single_keys["hkl_checkbox"]),
         sg.Radio("Above", "single_hkl", enable_events=True, key=single_keys["hkl_above"]),
         sg.Radio("Below", "single_hkl", default=True, enable_events=True, key=single_keys["hkl_below"])],
        checkbox_button_row("Show cumulative \u03C7\u00b2", "Options", False, single_keys["cchi2"]),
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="single_normalise_intensity_checkbox")],
        # [sg.Checkbox("Show error bars", enable_events=True, key="single_error_bars_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "single_x_scale_radio", default=True, enable_events=True, key=single_keys["x_scale_linear"]),
         sg.Radio("Sqrt", "single_x_scale_radio", enable_events=True, key=single_keys["x_scale_sqrt"]),
         sg.Radio("Log", "single_x_scale_radio", enable_events=True, key=single_keys["x_scale_log"])],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "single_y_scale_radio", default=True, enable_events=True, key=single_keys["y_scale_linear"]),
         sg.Radio("Sqrt", "single_y_scale_radio", enable_events=True, key=single_keys["y_scale_sqrt"]),
         sg.Radio("Log", "single_y_scale_radio", enable_events=True, key=single_keys["y_scale_log"])]
    ]

layout_single_right = \
    [
        [sg.Frame("Data", layout_single_data_chooser, key="single_data_chooser_frame")],
        [sg.Frame("Plot controls", layout_single_plot_control, key="single_plot_controls_frame")]
    ]

layout_single = \
    [
        [
            sg.Column(layout_single_left, pad=(0, 0), expand_x=True, expand_y=True),
            # sg.VerticalSeparator(),
            sg.Column(layout_single_right, key="single_right_column", pad=(0, 0), vertical_alignment="top")
        ]
    ]

#################################################################################################################
#
# --- stack tab
#
#################################################################################################################
stack_keys = {"x_axis": "stack_x_ordinate",
              "y_axis": "stack_y_ordinate",
              "offset_input": "stack_y_offset_input",
              "offset_value": "stack_y_offset_value",
              "hkl_checkbox": "stack_hkl_checkbox",
              "hkl_above": "stack_hkl_checkbox_above",
              "hkl_below": "stack_hkl_checkbox_below",
              "x_scale_linear": "stack_x_scale_linear",
              "x_scale_sqrt": "stack_x_scale_sqrt",
              "x_scale_log": "stack_x_scale_log",
              "y_scale_linear": "stack_y_scale_linear",
              "y_scale_sqrt": "stack_y_scale_sqrt",
              "y_scale_log": "stack_y_scale_log"}


def update_stack_element_disables(values, window):
    # enable all buttons and dropdowns
    for key in stack_keys.keys():
        window[stack_keys[key]].update(disabled=False)

    # disable buttons and dropdowns that need disabling
    #   If you've chosen an x-ordinate that
    #   doesn't allow hkl ticks, disable hkl checkbox and radio
    # also, I need to figure out how to do the hkl ticks the way I want to do them...
    if True or values[stack_keys["x_axis"]] in ["_pd_meas_time_of_flight", "_pd_meas_position"]:
        window[stack_keys["hkl_checkbox"]].update(disabled=True, value=False)
        window[stack_keys["hkl_above"]].update(disabled=True)
        window[stack_keys["hkl_below"]].update(disabled=True)


layout_stack_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="stack_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Canvas(key="stack_matplotlib_controls")]
    ]

layout_stack_plot_control = \
    [
        label_dropdown_row("X axis:", [], "", stack_keys["x_axis"]),
        label_dropdown_row("Y axis:", [], "", stack_keys["y_axis"]),
        # label_dropdown_button_row("Y axis:", "Options", y_list, y_list[0], "stack_y_ordinate"),
        [sg.T("Offset:"), sg.Input(default_text=100, size=(6, 1), enable_events=False, key=stack_keys["offset_input"]),
         sg.Button('Submit_offset', visible=False, bind_return_key=True, key=stack_keys["offset_value"], enable_events=True)],
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key=stack_keys["hkl_checkbox"]),
         sg.Radio("Above", "hkl", enable_events=True, key=stack_keys["hkl_above"]),
         sg.Radio("Below", "hkl", default=True, enable_events=True, key=stack_keys["hkl_below"])],
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="stack_normalise_intensity_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "stack_x_scale_radio", default=True, enable_events=True, key=stack_keys["x_scale_linear"]),
         sg.Radio("Sqrt", "stack_x_scale_radio", enable_events=True, key=stack_keys["x_scale_sqrt"]),
         sg.Radio("Log", "stack_x_scale_radio", enable_events=True, key=stack_keys["x_scale_log"])],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "stack_y_scale_radio", default=True, enable_events=True, key=stack_keys["y_scale_linear"]),
         sg.Radio("Sqrt", "stack_y_scale_radio", enable_events=True, key=stack_keys["y_scale_sqrt"]),
         sg.Radio("Log", "stack_y_scale_radio", enable_events=True, key=stack_keys["y_scale_log"])]
    ]

layout_stack_right = \
    [
        [sg.Frame("Plot controls", layout_stack_plot_control, key="stack_plot_controls_frame")]
    ]

layout_stack = \
    [
        [
            sg.Column(layout_stack_left, pad=(0, 0), expand_x=True, expand_y=True),
            # sg.VerticalSeparator(),
            sg.Column(layout_stack_right, key="stack_right_column", pad=(0, 0), vertical_alignment="top")
        ]
    ]
#
# #################################################################################################################
# #
# # --- surface tab
# #
# #################################################################################################################
surface_keys = {"x_axis": "surface_x_ordinate",
                "y_axis": "surface_y_ordinate",
                "z_axis": "surface_z_ordinate",
                "hkl_checkbox": "surface_hkl_checkbox",
                "x_scale_linear": "surface_x_scale_linear",
                "x_scale_sqrt": "surface_x_scale_sqrt",
                "x_scale_log": "surface_x_scale_log",
                "y_scale_linear": "surface_y_scale_linear",
                "y_scale_sqrt": "surface_y_scale_sqrt",
                "y_scale_log": "surface_y_scale_log",
                "z_scale_linear": "surface_z_scale_linear",
                "z_scale_sqrt": "surface_z_scale_sqrt",
                "z_scale_log": "surface_z_scale_log"}
surface_keys_with_buttons = ["z_axis"]
surface_buttons_keys = {k: surface_keys[k] + "_button" for k in surface_keys_with_buttons}
surface_buttons_values = {v: (k, i) for i, (k, v) in enumerate(surface_buttons_keys.items())}


def update_surface_element_disables(values, window):
    # enable all buttons and dropdowns
    for key in surface_keys.keys():
        window[surface_keys[key]].update(disabled=False)
    for key in surface_buttons_keys.keys():
        window[surface_buttons_keys[key]].update(disabled=False)

    # disable buttons and dropdowns that need disabling
    # window[surface_keys["y_axis"]].update(disabled=True)
    #   If you've chosen an x-ordinate that
    #   doesn't allow hkl ticks, disable hkl checkbox and radio
    # also, I need to figure out how to do the hkl ticks the way I want to do them...
    if values[surface_keys["x_axis"]] in ["_pd_meas_time_of_flight", "_pd_meas_position"]:
        window[surface_keys["hkl_checkbox"]].update(disabled=True, value=False)


layout_surface_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="surface_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Canvas(key="surface_matplotlib_controls")]
    ]

layout_surface_plot_control = \
    [
        label_dropdown_row("X axis:", [], "", surface_keys["x_axis"]),
        label_dropdown_row("Y axis:", ["Pattern number"], "Pattern number", surface_keys["y_axis"]),
        label_dropdown_button_row("Z axis:", "Options", [], "", surface_keys["z_axis"]),
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key=surface_keys["hkl_checkbox"])],
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="surface_normalise_intensity_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "surface_x_scale_radio", default=True, enable_events=True, key=surface_keys["x_scale_linear"]),
         sg.Radio("Sqrt", "surface_x_scale_radio", enable_events=True, key=surface_keys["x_scale_sqrt"]),
         sg.Radio("Log", "surface_x_scale_radio", enable_events=True, key=surface_keys["x_scale_log"])],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "surface_y_scale_radio", default=True, enable_events=True, key=surface_keys["y_scale_linear"]),
         sg.Radio("Sqrt", "surface_y_scale_radio", enable_events=True, key=surface_keys["y_scale_sqrt"]),
         sg.Radio("Log", "surface_y_scale_radio", enable_events=True, key=surface_keys["y_scale_log"])],
        [sg.Text("Z scale:"),
         sg.Radio("Linear", "surface_z_scale_radio", default=True, enable_events=True, key=surface_keys["z_scale_linear"]),
         sg.Radio("Sqrt", "surface_z_scale_radio", enable_events=True, key=surface_keys["z_scale_sqrt"]),
         sg.Radio("Log", "surface_z_scale_radio", enable_events=True, key=surface_keys["z_scale_log"])]
    ]

layout_surface_right = \
    [
        [sg.Frame("Plot controls", layout_surface_plot_control, key="surface_plot_controls_frame")]
    ]

layout_surface = \
    [
        [
            sg.Column(layout_surface_left, pad=(0, 0), expand_x=True, expand_y=True),
            # sg.VerticalSeparator(),
            sg.Column(layout_surface_right, key="surface_right_column", pad=(0, 0), vertical_alignment="top")
        ]
    ]

#################################################################################################################
#
# --- Window layout, generation, and expansion
#
#################################################################################################################

layout_file_chooser = \
    [[
        sg.FilesBrowse(button_text="Load file",
                       target='file_string',
                       key="load_files",
                       file_types=(('CIF Files', '*.cif'),
                                   ('State Files', '*.state'),
                                   ('ALL Files', '*.*')),
                       enable_events=True),  # may need to implement OneLineProgressMeter on loading and parsing CIF
        sg.In(key='file_string', visible=False, enable_events=True),
        sg.T(key="file_string_name")
    ]]

layout = \
    [
        layout_file_chooser,
        [
            sg.TabGroup(
                [[
                    sg.Tab("Single", layout_single, key="single_tab"),
                    sg.Tab("Stack", layout_stack, key="stack_tab"),
                    sg.Tab("Surface", layout_surface, key="surface_tab")
                ]],
                tab_location='topleft',
                key='tab-change',
                enable_events=True,
                expand_x=True, expand_y=True)
        ]
    ]


def open_cif_popup(text):
    layout = [[sg.T(text)]]
    window = sg.Window("Reading CIF...", layout)
    window.read(timeout=0)
    return window


#################################################################################################################
#
# --- setup the window and all button disable things
#
#################################################################################################################
def gui():
    global single_figure_agg, stack_figure_agg, surface_figure_agg, surface_z_color

    window = sg.Window("pdCIFplotter", layout, finalize=True, use_ttk_buttons=True, resizable=True)

    check_msg = check_packages()
    if check_msg != "":
        sg.Print(check_msg)

    # set all the dropdowns and buttons to disabled before I have data to do things to.
    for key in single_keys.keys():
        window[single_keys[key]].update(disabled=True)
    for key in single_buttons_keys.keys():
        window[single_buttons_keys[key]].update(disabled=True)
    for key in stack_keys.keys():
        window[stack_keys[key]].update(disabled=True)
    for key in surface_keys.keys():
        window[surface_keys[key]].update(disabled=True)
    for key in surface_buttons_keys.keys():
        window[surface_buttons_keys[key]].update(disabled=True)

    ##################################################################################################################
    #
    # --- The event loop that controls everything!
    #
    #################################################################################################################

    while True:
        event, values = window.read()

        try:
            the_value = values[event]
        except (KeyError, TypeError):
            the_value = "__none__"

        print("-----------------\n", event, ":", the_value, " --- ", values, "\n-----------------")

        replot_single = False
        replot_stack = False
        replot_surface = False

        # this is a big if/elif that controls the entire gui flow
        if event is None:
            break  # Exit the program

        # ----------
        # load file
        # ----------
        elif event == "file_string":
            files_str = values['file_string']
            if files_str == "":
                continue  # the file wasn't chosen, so just keep looping

            # you've loaded a new file, so I need to scrub all variables
            reset_globals()

            try:
                popup = open_cif_popup("Now opening your CIF file.\nPlease wait...")
                read_cif(files_str)
            except Exception as e:
                # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)
                msg = f"There has been an error in reading the CIF file. Please check that it is of a valid format before continuing. Some information may be apparant from the text below:\n\n{e}"
                sg.Print(msg)
                print(e)
                continue
            finally:
                popup.close()
                pass

            pc.pretty(cif)

            window["file_string"].update(value=[])
            window["file_string_name"].update(value=values["file_string"])

            ###
            # Update the single elements
            ###
            initialise_pattern_and_dropdown_lists()
            # update single_data combo information
            pattern = single_data_list[0]
            window[single_keys["data"]].update(disabled=False)
            window[single_keys["data"]].update(values=single_data_list, value=pattern)

            # update xy combo dropdown information
            window[single_keys["x_axis"]].update(values=single_dropdown_lists[pattern]["x_values"], value=single_dropdown_lists[pattern]["x_value"])
            window[single_keys["yobs"]].update(values=single_dropdown_lists[pattern]["yobs_values"], value=single_dropdown_lists[pattern]["yobs_value"])
            window[single_keys["ycalc"]].update(values=single_dropdown_lists[pattern]["ycalc_values"], value=single_dropdown_lists[pattern]["ycalc_value"])
            window[single_keys["ybkg"]].update(values=single_dropdown_lists[pattern]["ybkg_values"], value=single_dropdown_lists[pattern]["ybkg_value"])

            ###
            # Update the stack elements
            ###
            stack_figure_agg = None
            initialise_stack_xy_lists()
            window[stack_keys["x_axis"]].update(values=stack_x_ordinates, value=stack_x_ordinates[0])
            window[stack_keys["y_axis"]].update(values=stack_y_ordinates[stack_x_ordinates[0]], value=stack_y_ordinates[stack_x_ordinates[0]][0])
            ###
            # Update the surface elements
            ###
            surface_figure_agg = None
            initialise_surface_xz_lists()
            window[surface_keys["x_axis"]].update(values=surface_x_ordinates, value=surface_x_ordinates[0])
            window[surface_keys["z_axis"]].update(values=surface_z_ordinates[surface_x_ordinates[0]], value=surface_z_ordinates[surface_x_ordinates[0]][0])

            ###
            # At the very end:
            ###

            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_single_element_disables(pattern, values, window)
            update_stack_element_disables(values, window)
            update_surface_element_disables(values, window)
            _, values = window.read(timeout=0)
            # plot first pattern
            replot_single = True

        # --------------------------------------------------------------------------------------
        #
        #  single window things
        #
        # --------------------------------------------------------------------------------------
        elif event == "tab-change" and values[event] == "single_tab" and single_figure_agg is None:
            replot_single = True

        elif event == single_keys["data"]:
            replot_single = True
            pattern = values[event]
            # because I'm changing the pattern I'm plotting, there may be different data available to plot
            #  This will change the options for the dropdown boxes and the like
            # update the dropdownlists
            window[single_keys["x_axis"]].update(values=single_dropdown_lists[pattern]["x_values"], value=single_dropdown_lists[pattern]["x_value"])
            window[single_keys["yobs"]].update(values=single_dropdown_lists[pattern]["yobs_values"], value=single_dropdown_lists[pattern]["yobs_value"])
            window[single_keys["ycalc"]].update(values=single_dropdown_lists[pattern]["ycalc_values"], value=single_dropdown_lists[pattern]["ycalc_value"])
            window[single_keys["ybkg"]].update(values=single_dropdown_lists[pattern]["ybkg_values"], value=single_dropdown_lists[pattern]["ybkg_value"])

            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_single_element_disables(pattern, values, window)
            _, values = window.read(timeout=0)

        elif event in list(single_keys.values())[1:]:  # ie if I click anything apart from the data chooser
            replot_single = True
            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_single_element_disables(pattern, values, window)
            _, values = window.read(timeout=0)

        elif event in list(single_buttons_keys.values()):
            y_ordinate_styling_popup(f"{single_buttons_values[event][0]} styling",
                                     y_style[single_buttons_values[event][1]][0],
                                     y_style[single_buttons_values[event][1]][1],
                                     y_style[single_buttons_values[event][1]][2],
                                     y_style[single_buttons_values[event][1]][3],
                                     f"{event}-popupkey",
                                     window)
        elif event in [v + "-popupkey-popup-ok" for v in single_buttons_keys.values()]:
            button = event.replace('-popupkey-popup-ok', '')

            # update the style values
            y_style[single_buttons_values[button][1]] = \
                [values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-color'],
                 values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-markerstyle'],
                 values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-linestyle'],
                 values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-size']]
            replot_single = True

        # --------------------------------------------------------------------------------------
        #  stack window things
        # --------------------------------------------------------------------------------------

        elif event == "tab-change" and values[event] == "stack_tab" and stack_figure_agg is None:
            replot_stack = True

        elif event == stack_keys["x_axis"]:
            replot_stack = True
            window[stack_keys["y_axis"]].update(values=stack_y_ordinates[the_value], value=stack_y_ordinates[the_value][0])
            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_stack_element_disables(values, window)
            _, values = window.read(timeout=0)

        elif event in list(stack_keys.values())[1:]:  # ie if I click anything apart from the x-axis
            replot_stack = True
            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_stack_element_disables(values, window)
            _, values = window.read(timeout=0)

        # --------------------------------------------------------------------------------------
        #  surface window things
        # --------------------------------------------------------------------------------------
        elif event == "tab-change" and values[event] == "surface_tab" and surface_figure_agg is None:
            replot_surface = True

        elif event == surface_keys["x_axis"]:
            replot_surface = True
            # update the dropdownlists
            window[surface_keys["z_axis"]].update(values=surface_z_ordinates[the_value], value=surface_z_ordinates[the_value][0])
            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_surface_element_disables(values, window)
            _, values = window.read(timeout=0)

        elif event in list(surface_keys.values())[1:]:  # ie if I click anything apart from the x-axis
            replot_surface = True
            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_surface_element_disables(values, window)
            _, values = window.read(timeout=0)

        elif event == "surface_z_ordinate_button":
            z_ordinate_styling_popup("Surface Z colour scale", surface_z_color, "surface_z_color", window)
        elif event == "surface_z_color-popup-ok":
            surface_z_color = values["surface_z_color-popup-ok"]['surface_z_color-popup-color']
            replot_surface = True
        # end of window events

        # at the bottom of the event loop, I pop into the replots for the three plots.
        # as there are multiple reasons to replot, I've put it down here so I only
        # need to write it once.
        if replot_single and cif != {}:
            pattern = values[single_keys["data"]]
            # # update the value of all the dropdown lists
            x_ordinate = values[single_keys["x_axis"]]
            yobs = values[single_keys["yobs"]]
            ycalc = values[single_keys["ycalc"]]
            ybkg = values[single_keys["ybkg"]]

            # construct axis scale dictionary
            x_axes = [values[single_keys["x_scale_linear"]], values[single_keys["x_scale_sqrt"]], values[single_keys["x_scale_log"]]]
            y_axes = [values[single_keys["y_scale_linear"]], values[single_keys["y_scale_sqrt"]], values[single_keys["y_scale_log"]]]
            axis_words = ["linear", "sqrt", "log"]
            single_axis_scale = {}
            single_axis_scale["x"] = [word for word, scale in zip(axis_words, x_axes) if scale][0]
            single_axis_scale["y"] = [word for word, scale in zip(axis_words, y_axes) if scale][0]
            try:
                single_update_plot(pattern,
                                   x_ordinate,
                                   [yobs, ycalc, ybkg],
                                   values[single_keys["hkl_checkbox"]],
                                   values[single_keys["ydiff"]],
                                   values[single_keys["cchi2"]],
                                   single_axis_scale,
                                   window)
            except (IndexError, ValueError) as e:
                pass

        if replot_stack:
            x_ordinate = values[stack_keys["x_axis"]]
            y_ordinate = values[stack_keys["y_axis"]]
            offset = float(values[stack_keys["offset_input"]])
            plot_hkls = values[stack_keys["hkl_checkbox"]]
            # construct axis scale dictionary
            x_axes = [values[stack_keys["x_scale_linear"]], values[stack_keys["x_scale_sqrt"]], values[stack_keys["x_scale_log"]]]
            y_axes = [values[stack_keys["y_scale_linear"]], values[stack_keys["y_scale_sqrt"]], values[stack_keys["y_scale_log"]]]
            axis_words = ["linear", "sqrt", "log"]
            stack_axis_scale = {}
            stack_axis_scale["x"] = [word for word, scale in zip(axis_words, x_axes) if scale][0]
            stack_axis_scale["y"] = [word for word, scale in zip(axis_words, y_axes) if scale][0]
            try:
                stack_update_plot(x_ordinate, y_ordinate, offset, plot_hkls, stack_axis_scale, window)
            except (IndexError, ValueError) as e:
                pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

        if replot_surface:
            x_ordinate = values["surface_x_ordinate"]
            z_ordinate = values["surface_z_ordinate"]
            plot_hkls = values[surface_keys["hkl_checkbox"]]
            # construct axis scale dictionary
            x_axes = [values[surface_keys["x_scale_linear"]], values[surface_keys["x_scale_sqrt"]], values[surface_keys["x_scale_log"]]]
            y_axes = [values[surface_keys["y_scale_linear"]], values[surface_keys["y_scale_sqrt"]], values[surface_keys["y_scale_log"]]]
            z_axes = [values[surface_keys["z_scale_linear"]], values[surface_keys["z_scale_sqrt"]], values[surface_keys["z_scale_log"]]]
            axis_words = ["linear", "sqrt", "log"]
            surface_axis_scale = {}
            surface_axis_scale["x"] = [word for word, scale in zip(axis_words, x_axes) if scale][0]
            surface_axis_scale["y"] = [word for word, scale in zip(axis_words, y_axes) if scale][0]
            surface_axis_scale["z"] = [word for word, scale in zip(axis_words, z_axes) if scale][0]
            try:
                surface_update_plot(x_ordinate, z_ordinate, plot_hkls, surface_axis_scale, window)
            except (IndexError, ValueError) as e:
                pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)


if __name__ == "__main__":
    gui()
