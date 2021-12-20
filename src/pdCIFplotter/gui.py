# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 20:56:13 2021

@author: Matthew Rowles
"""

import tkinter
import PySimpleGUI as sg

import pdCIFplotter as pcp
from pdCIFplotter import parse_cif, plot_cif
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.figure as mf
import matplotlib.axes as ma
import matplotlib as mpl
from typing import List, Union
import sys

# from timeit import default_timer as timer  # use as start = timer() ...  end = timer()

DEBUG = False

# Potential themes that work for me.
THEME_NUMBER = 2
MY_THEMES = ["Default1", "GrayGrayGray", "Reddit", "SystemDefault1", "SystemDefaultForReal"]
sg.theme(MY_THEMES[THEME_NUMBER])

print("somestuff")
print(f"{mpl.__version__=}")
if mpl.__version__ <= "3.4.3":  # matplotlib bug workaround: https://github.com/matplotlib/matplotlib/issues/21875
    sg.set_options(dpi_awareness=True)

# global parameters
action_column_width = 30
canvas_x = 600
canvas_y = canvas_x // 1.6

single_fig: mf.Figure = None
single_ax: ma.Axes = None
single_figure_agg: FigureCanvasTkAgg = None

stack_fig: mf.Figure = None
stack_figure_agg: FigureCanvasTkAgg = None

surface_fig: mf.Figure = None
surface_figure_agg: FigureCanvasTkAgg = None

cif = {}  # the cif dictionary from my parsing
plotcif: plot_cif.PlotCIF = None
single_data_list = []  # a list of all pattern blocknames in the cif
single_dropdown_lists = {}  # all the appropriate x and y ordinates for each pattern

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
    global stack_fig, stack_figure_agg
    global surface_fig, surface_figure_agg

    global cif
    global plotcif
    global single_data_list, single_dropdown_lists
    global stack_x_ordinates, stack_y_ordinates
    global surface_x_ordinates, surface_z_ordinates

    single_fig = None
    single_ax = None
    single_figure_agg = None

    stack_fig = None
    stack_figure_agg = None

    surface_fig = None
    surface_figure_agg = None

    cif = {}  # the cif dictionary from my parsing
    plotcif = None
    single_data_list = []  # a list of all pattern blocknames in the cif
    single_dropdown_lists = {}  # all the appropriate x and y ordinates for each pattern

    stack_x_ordinates = []
    stack_y_ordinates = {}

    surface_x_ordinates = []
    surface_z_ordinates = {}


LINE_MARKER_COLORS = plot_cif.LINE_MARKER_COLORS
MARKER_STYLES = plot_cif.MARKER_STYLES
LINE_STYLES = plot_cif.LINE_STYLES
LINE_MARKER_SIZE = plot_cif.LINE_MARKER_SIZE
SURFACE_COLOR_MAPS = plot_cif.SURFACE_COLOR_MAPS

# these lists contain all the possible x and y ordinate data items that I want to worry about in this program
# the last few entries in each list correspond to values that could potentially be calc'd from the given
# information, but were not presented in the CIF.
COMPLETE_X_LIST = parse_cif.ParseCIF.COMPLETE_X_LIST
OBSERVED_Y_LIST = parse_cif.ParseCIF.OBSERVED_Y_LIST
CALCULATED_Y_LIST = parse_cif.ParseCIF.CALCULATED_Y_LIST
BACKGROUND_Y_LIST = parse_cif.ParseCIF.BACKGROUND_Y_LIST
COMPLETE_XY_PLAINTEXT_DICT = {"_pd_meas_2theta_scan": "\u00B0 2\u03b8 measured",
                              "_pd_proc_2theta_corrected": "\u00B0 2\u03b8 corrected",
                              "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                              "_pd_meas_position": "Position (mm)",
                              "_pd_proc_energy_incident": "Incident energy (eV)",
                              "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                              "_pd_proc_d_spacing": "d spacing (\u212b)",
                              "_pd_proc_recip_len_Q": "q (1/\u212b)",
                              "d": "d spacing (calc'd from 2\u03b8 or q) (\u212b)",
                              "q": "q (calc'd from 2\u03b8 or d) (1/\u212b)",
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
        elif print_values:
            print('\t' * (indent + 1) + str(value))


def single_update_plot(pattern, x_ordinate: str, y_ordinates: list,
                       plot_hkls: dict, plot_diff: bool, plot_cchi2: bool, plot_norm_int: bool,
                       axis_scale: dict, window):
    global single_figure_agg, single_fig, single_ax

    single_fig, single_ax, x_zoom, y_zoom = \
        plotcif.single_update_plot(pattern, x_ordinate, y_ordinates,
                                   plot_hkls, plot_diff, plot_cchi2, plot_norm_int,
                                   axis_scale, single_fig, single_ax)

    single_figure_agg = draw_figure_w_toolbar(window["single_plot"].TKCanvas, single_fig,
                                              window["single_matplotlib_controls"].TKCanvas,
                                              True)
    if x_zoom:
        single_ax.set_xlim(x_zoom)  # restore zoom
        single_ax.set_ylim(y_zoom)


def stack_update_plot(x_ordinate: str, y_ordinate: str, offset: float, plot_hkls: dict, stack_norm_plot: dict, axis_scale: dict, window):
    global stack_figure_agg, stack_fig

    stack_fig = plotcif.stack_update_plot(x_ordinate, y_ordinate, offset, plot_hkls, stack_norm_plot, axis_scale, stack_fig)

    stack_figure_agg = draw_figure_w_toolbar(window["stack_plot"].TKCanvas, stack_fig,
                                             window["stack_matplotlib_controls"].TKCanvas)


def surface_update_plot(x_ordinate: str, y_ordinate: str, z_ordinate: str, plot_hkls: bool, plot_norm: dict, axis_scale: dict, window):
    global surface_figure_agg, surface_fig

    surface_fig = plotcif.surface_update_plot(x_ordinate, y_ordinate, z_ordinate, plot_hkls, plot_norm, axis_scale, surface_fig)

    surface_figure_agg = draw_figure_w_toolbar(window["surface_plot"].TKCanvas, surface_fig,
                                               window["surface_matplotlib_controls"].TKCanvas)


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
# https://github.com/PySimpleGUI/PySimpleGUI/issues/3989#issuecomment-794005240
def draw_figure_w_toolbar(canvas: tkinter.Canvas, figure: mf.Figure, canvas_toolbar: tkinter.Canvas, make_new_home: bool = False) -> FigureCanvasTkAgg:
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(figure, master=canvas)
    figure_canvas_agg.draw()
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    toolbar.config(background=sg.theme_background_color())
    toolbar._message_label.config(background=sg.theme_background_color())  # this is to do with the XY text that comes up when the cursor is over the plot
    toolbar.winfo_children()[-2].config(background=sg.theme_background_color())  # https://stackoverflow.com/a/69955540/36061
    # debug(f"{toolbar._message_label.config().keys()=}")
    # debug(f"{toolbar.config().keys()=}")
    toolbar.update()
    if make_new_home:
        toolbar.push_current()
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    return figure_canvas_agg


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)


def y_ordinate_styling_popup(window_title: str, color_default: str, marker_styles_default: str, line_style_default: str, size_default: str, key: str, window):
    layout_def = \
        [
            [sg.Text("What line/marker colour, marker style, line style, and line/marker size do you want?")],
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


def z_ordinate_styling_popup(window_title: str, color_default: str, key: str, window):
    layout_def = [
        [sg.Text("What surface colour do you want?")],
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

def make_list_for_ordinate_dropdown(complete_list: List[str], possible_list: List[str], add_none: bool = True) -> List[str]:
    used_list = [t for t in complete_list if t in possible_list]
    if add_none:
        used_list.append("None")
    return used_list


def x_axis_title(x_ordinate: str, wavelength: float = None) -> str:
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


def read_cif(filename: str) -> None:
    global cif
    cif = parse_cif.ParseCIF(filename).get_processed_cif()
    if len(cif) == 0:
        raise ValueError("No diffraction pattern found in CIF.")


def make_xy_dropdown_list(master_list: List[str], difpat: str, add_none: bool = True) -> List[str]:
    return make_list_for_ordinate_dropdown(master_list, cif[difpat].keys(), add_none=add_none)


def cif_get_this_else_that(cif: dict, dataname: str, that: Union[List[str], str]):
    if dataname in cif:
        return cif[dataname]
    else:
        return that


def initialise_pattern_and_dropdown_lists() -> None:
    global single_data_list, single_dropdown_lists
    single_data_list = [pattern for pattern in cif]
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


def initialise_stack_xy_lists() -> None:
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
        for x_ordinate in parse_cif.ParseCIF.COMPLETE_X_LIST:
            if x_ordinate in cif[pattern]:
                if x_ordinate not in stack_x_ordinates:
                    stack_x_ordinates.append(x_ordinate)
                    stack_y_ordinates[x_ordinate] = []
                for y_ordinate in parse_cif.ParseCIF.COMPLETE_Y_LIST:
                    if y_ordinate in cif[pattern] and y_ordinate not in stack_y_ordinates[x_ordinate]:
                        stack_y_ordinates[x_ordinate].append(y_ordinate)


def initialise_surface_xz_lists() -> None:
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
        for x_ordinate in parse_cif.ParseCIF.COMPLETE_X_LIST:
            if x_ordinate in cif[pattern]:
                if x_ordinate not in surface_x_ordinates:
                    surface_x_ordinates.append(x_ordinate)
                    surface_z_ordinates[x_ordinate] = []
                for y_ordinate in parse_cif.ParseCIF.COMPLETE_Y_LIST:
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


def label_dropdown_row(label: str, values: List[str], default: str, key: str) -> List:
    return [sg.T(label),
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True, size=30)]


def label_dropdown_button_row(label: str, button_text: str, values: List[str], default: str, key: str) -> List:
    return [sg.T(label),
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True, size=30),
            sg.Button(button_text=button_text, key=key + "_button")]


def checkbox_button_row(checkbox_text: str, button_text: str, default: Union[str, bool], key: str) -> List:
    return [sg.Checkbox(checkbox_text, enable_events=True, default=default, key=key),
            sg.Stretch(),
            sg.Button(button_text=button_text, key=key + "_button")]


#################################################################################################################
#
# --- single tab
#
#################################################################################################################
single_keys = {"data": "single_data_chooser",  # this entry must remain at the beginning
               "next_data": "single_next_data",
               "prev_data": "single_prev_data",
               "x_axis": "single_x_ordinate",
               "yobs": "single_yobs_ordinate",
               "ycalc": "single_ycalc_ordinate",
               "ybkg": "single_ybkg_ordinate",
               "ydiff": "single_ydiff_checkbox",
               "hkl_checkbox": "single_hkl_checkbox",
               "hkl_above": "single_hkl_checkbox_above",
               "hkl_below": "single_hkl_checkbox_below",
               "cchi2": "single_cchi2_checkbox",
               "norm_int": "single_norm_int_checkbox",
               "x_scale_linear": "single_x_scale_linear",
               "x_scale_sqrt": "single_x_scale_sqrt",
               "x_scale_log": "single_x_scale_log",
               "y_scale_linear": "single_y_scale_linear",
               "y_scale_sqrt": "single_y_scale_sqrt",
               "y_scale_log": "single_y_scale_log"}

single_keys_with_buttons = ["yobs", "ycalc", "ybkg", "ydiff", "cchi2"]
single_buttons_keys = {k: single_keys[k] + "_button" for k in single_keys_with_buttons}
single_buttons_values = {v: k for k, v in single_buttons_keys.items()}


def update_single_element_disables(pattern: str, values: dict, window: sg.Window) -> None:
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
    if len(single_data_list) <= 1:
        window[single_keys["next_data"]].update(disabled=True)
        window[single_keys["prev_data"]].update(disabled=True)
    #   If there isn't at least one hkl list, or you've chosen an x-ordinate that
    #   doesn't allow hkl ticks, disable hkl checkbox and radio
    if "str" not in cif[pattern] or values[single_keys["x_axis"]] in ["_pd_meas_time_of_flight", "_pd_meas_position"]:
        window[single_keys["hkl_checkbox"]].update(disabled=True, value=False)
        window[single_keys["hkl_above"]].update(disabled=True)
        window[single_keys["hkl_below"]].update(disabled=True)
    # if there is at least one str
    elif "str" in cif[pattern]:
        x_ordinate = values[single_keys["x_axis"]]  # get the x-ordinate currently being display
        # if all phases don't have hkls, then disable the box, otherwise enable it, and rely on the plot_cif
        # routines to catch the non-existence of the hkls and the handle them gracefully
        if all(not ((x_ordinate in ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected"] and "refln_2theta" in cif[pattern]["str"][phase]) or
                    (x_ordinate in ["_pd_proc_d_spacing", "_pd_proc_recip_len_Q", "d", "q"] and "_refln_d_spacing" in cif[pattern]["str"][phase])) for phase in
               cif[pattern]["str"]):
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
                 size=39,
                 enable_events=True,
                 key=single_keys["data"],
                 readonly=True),
        sg.Stretch(),
        sg.B("<", enable_events=True, key=single_keys["prev_data"]),
        sg.B(">", enable_events=True, key=single_keys["next_data"]),

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
        [sg.Checkbox("Normalise all intensities to counts", enable_events=True, default=False, key=single_keys["norm_int"])],
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
            sg.VerticalSeparator(),
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
              "norm_int": "stack_norm_int_checkbox",
              "x_scale_linear": "stack_x_scale_linear",
              "x_scale_sqrt": "stack_x_scale_sqrt",
              "x_scale_log": "stack_x_scale_log",
              "y_scale_linear": "stack_y_scale_linear",
              "y_scale_sqrt": "stack_y_scale_sqrt",
              "y_scale_log": "stack_y_scale_log"}


def update_stack_element_disables(values: dict, window: sg.Window) -> None:
    # enable all buttons and dropdowns
    for key in stack_keys.keys():
        window[stack_keys[key]].update(disabled=False)

    # disable buttons and dropdowns that need disabling
    #   If you've chosen an x-ordinate that
    #   doesn't allow hkl ticks, disable hkl checkbox and radio
    # also, I need to figure out how to do the hkl ticks the way I want to do them...
    if values[stack_keys["x_axis"]] in ["_pd_meas_time_of_flight", "_pd_meas_position"]:
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
        [sg.Checkbox("Normalise intensity to counts", enable_events=True, default=False, key=stack_keys["norm_int"])],
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
            sg.VerticalSeparator(),
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
                "norm_int": "surface_norm_int_checkbox",
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


def update_surface_element_disables(values: dict, window: sg.Window) -> None:
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

    # always disable the y-ordinate chooser. Will need a large upgrade to change that ont
    window[surface_keys["y_axis"]].update(disabled=True)


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
        [sg.Checkbox("Normalise intensity to counts", enable_events=True, default=False, key=surface_keys["norm_int"])],
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
            sg.VerticalSeparator(),
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
                                   # ('State Files', '*.state'),
                                   ('ALL Files', '*.*')),
                       enable_events=True),  # may need to implement OneLineProgressMeter on loading and parsing CIF
        sg.In(key='file_string', visible=False, enable_events=True),
        sg.T(key="file_string_name"),
        sg.Stretch(),
        sg.T(pcp.__version__)
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


def open_cif_popup(text: str, icon: str) -> sg.Window:
    m_layout = [[sg.T(text)]]
    window = sg.Window("Reading CIF...", m_layout, icon=icon)
    window.read(timeout=0)
    return window


#################################################################################################################
#
# --- setup the window and all button disable things
#
#################################################################################################################
def gui() -> None:
    global plotcif, single_figure_agg, stack_figure_agg, surface_figure_agg

    # This bit gets the taskbar icon working properly in Windows
    # https://github.com/PySimpleGUI/PySimpleGUI/issues/2722#issuecomment-852923088
    if sys.platform.startswith('win'):
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'CompanyName.ProductName.SubProduct.VersionInformation')  # Arbitrary string

    icon = b'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'
    window = sg.Window("pdCIFplotter", layout, finalize=True, use_ttk_buttons=True, resizable=True, icon=icon)

    # check_msg = check_packages()
    # if check_msg != "":
    #     sg.Print(check_msg)

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

        debug(f"-----------------\n{event}: {the_value} --- {values}\n-----------------")

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
                popup = open_cif_popup("Now opening your CIF file.\nPlease wait...", icon)
                read_cif(files_str)
                plotcif = plot_cif.PlotCIF(cif, canvas_x, canvas_y)
            except Exception as e:
                # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)
                msg = f"There has been an error in reading the CIF file. Please check that it is of a valid format before continuing. Some information may be apparant from the text below:\n\n{e}"
                sg.Print(msg)
                print(e)
                continue
            finally:
                popup.close()

            if DEBUG:
                parse_cif.pretty(cif)

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

        elif event in (single_keys["prev_data"], single_keys["next_data"]):
            replot_single = True
            single_current_data: str = values[single_keys["data"]]
            single_current_data_list: List[str] = window[single_keys["data"]].Values
            single_data_index = single_current_data_list.index(single_current_data)
            if event == single_keys["prev_data"]:
                single_data_index -= 1
            else:
                single_data_index += 1
            single_data_index %= len(single_current_data_list)
            pattern = single_current_data_list[single_data_index]

            window[single_keys["data"]].update(value=pattern)
            window[single_keys["x_axis"]].update(values=single_dropdown_lists[pattern]["x_values"], value=single_dropdown_lists[pattern]["x_value"])
            window[single_keys["yobs"]].update(values=single_dropdown_lists[pattern]["yobs_values"], value=single_dropdown_lists[pattern]["yobs_value"])
            window[single_keys["ycalc"]].update(values=single_dropdown_lists[pattern]["ycalc_values"], value=single_dropdown_lists[pattern]["ycalc_value"])
            window[single_keys["ybkg"]].update(values=single_dropdown_lists[pattern]["ybkg_values"], value=single_dropdown_lists[pattern]["ybkg_value"])

            # push all the window value updates and then update the enable/disable, and then push again
            _, values = window.read(timeout=0)
            update_single_element_disables(pattern, values, window)
            _, values = window.read(timeout=0)

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
            y_ordinate_styling_popup(f"{single_buttons_values[event]} styling",
                                     plotcif.single_y_style[single_buttons_values[event]]["color"],
                                     plotcif.single_y_style[single_buttons_values[event]]["marker"],
                                     plotcif.single_y_style[single_buttons_values[event]]["linestyle"],
                                     plotcif.single_y_style[single_buttons_values[event]]["linewidth"],
                                     f"{event}-popupkey",
                                     window)

        elif event in [v + "-popupkey-popup-ok" for v in single_buttons_keys.values()]:
            button = event.replace('-popupkey-popup-ok', '')

            # update the style values
            plotcif.single_y_style[single_buttons_values[button]]["color"] = values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-color']
            plotcif.single_y_style[single_buttons_values[button]]["marker"] = values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-markerstyle']
            plotcif.single_y_style[single_buttons_values[button]]["linestyle"] = values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-linestyle']
            plotcif.single_y_style[single_buttons_values[button]]["linewidth"] = values[f"{button}-popupkey-popup-ok"][f'{button}-popupkey-popup-size']
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
            z_ordinate_styling_popup("Surface Z colour scale", plotcif.surface_z_color, "surface_z_color", window)
        elif event == "surface_z_color-popup-ok":
            plotcif.surface_z_color = values["surface_z_color-popup-ok"]['surface_z_color-popup-color']
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
            single_axis_scale = {
                'x': [word for word, scale in zip(axis_words, x_axes) if scale][0],
                'y': [word for word, scale in zip(axis_words, y_axes) if scale][0],
            }

            # construct hkl checkbox dictionary
            plot_hkls = {"above": values[single_keys["hkl_checkbox"]] and values[single_keys["hkl_above"]],
                         "below": values[single_keys["hkl_checkbox"]] and values[single_keys["hkl_below"]]}
            try:
                single_update_plot(pattern,
                                   x_ordinate,
                                   [yobs, ycalc, ybkg],
                                   plot_hkls,
                                   values[single_keys["ydiff"]],
                                   values[single_keys["cchi2"]],
                                   values[single_keys["norm_int"]],
                                   single_axis_scale,
                                   window)
            except (IndexError, ValueError) as e:
                print(e)  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

        if replot_stack and cif != {}:
            x_ordinate = values[stack_keys["x_axis"]]
            y_ordinate = values[stack_keys["y_axis"]]
            offset = float(values[stack_keys["offset_input"]])
            plot_hkls = values[stack_keys["hkl_checkbox"]]
            # construct axis scale dictionary
            x_axes = [values[stack_keys["x_scale_linear"]], values[stack_keys["x_scale_sqrt"]], values[stack_keys["x_scale_log"]]]
            y_axes = [values[stack_keys["y_scale_linear"]], values[stack_keys["y_scale_sqrt"]], values[stack_keys["y_scale_log"]]]
            axis_words = ["linear", "sqrt", "log"]
            stack_axis_scale = {
                'x': [word for word, scale in zip(axis_words, x_axes) if scale][0],
                'y': [word for word, scale in zip(axis_words, y_axes) if scale][0]
            }
            # construct hkl checkbox dictionary
            plot_hkls = {"above": values[stack_keys["hkl_checkbox"]] and values[stack_keys["hkl_above"]],
                         "below": values[stack_keys["hkl_checkbox"]] and values[stack_keys["hkl_below"]]}

            stack_norm_plot = {"norm_int": values[stack_keys["norm_int"]],
                               "y_ordinate_for_norm": window[stack_keys['y_axis']].Values[0]}
            try:
                stack_update_plot(x_ordinate,
                                  y_ordinate,
                                  offset,
                                  plot_hkls,
                                  stack_norm_plot,
                                  stack_axis_scale,
                                  window)
            except (IndexError, ValueError) as e:
                print(e)  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

        if replot_surface and cif != {}:
            x_ordinate = values["surface_x_ordinate"]
            z_ordinate = values["surface_z_ordinate"]
            plot_hkls = values[surface_keys["hkl_checkbox"]]
            # construct axis scale dictionary
            x_axes = [values[surface_keys["x_scale_linear"]], values[surface_keys["x_scale_sqrt"]], values[surface_keys["x_scale_log"]]]
            y_axes = [values[surface_keys["y_scale_linear"]], values[surface_keys["y_scale_sqrt"]], values[surface_keys["y_scale_log"]]]
            z_axes = [values[surface_keys["z_scale_linear"]], values[surface_keys["z_scale_sqrt"]], values[surface_keys["z_scale_log"]]]
            axis_words = ["linear", "sqrt", "log"]
            surface_axis_scale = {
                'x': [word for word, scale in zip(axis_words, x_axes) if scale][0],
                'y': [word for word, scale in zip(axis_words, y_axes) if scale][0],
                'z': [word for word, scale in zip(axis_words, z_axes) if scale][0],
            }
            surface_norm_plot = {"norm_int": values[surface_keys["norm_int"]],
                                 "z_ordinate_for_norm": window[surface_keys['z_axis']].Values[0]}

            try:
                surface_update_plot(x_ordinate,
                                    "Pattern number",
                                    z_ordinate,
                                    plot_hkls,
                                    surface_norm_plot,
                                    surface_axis_scale,
                                    window)
            except (IndexError, ValueError) as e:
                print(e)  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)


if __name__ == "__main__":
    gui()
