# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 20:56:13 2021

@author: 184277J
"""

import PySimpleGUI as sg
import numpy as np
import pandas as pd
# import ntpath
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.collections import LineCollection
import matplotlib.colors as mc  # a lot of colour choices in here to use

import time

# Potential themes that work for me.  #reddit is the only one that doesn't jitter...  ?
MY_THEMES = ["Default1", "GrayGrayGray", "Reddit", "SystemDefault1", "SystemDefaultForReal"]
sg.theme(MY_THEMES[2])
sg.set_options(dpi_awareness=True)

# import traceback
# import sys


# global parameters
action_column_width = 30
canvas_x = 600  # 1200
canvas_y = 300  # 700
plot_x = canvas_x
plot_y = canvas_y

single_fig = None
single_ax = None
single_figure_agg = None
single_xlims = None
single_ylims = None
single_unzoom = None
single_ax_scale = 0.05  # for unzooming calculations
y_style = [["mediumblue", "+", "none", "2"],
           ["red", None, "solid", "1"],
           ["gray", None, "solid", "2"],
           ["lightgrey", None, "solid", "2"]]

stack_fig = None
stack_ax = None
stack_figure_agg = None
stack_xlims = None
stack_ylims = None
stack_unzoom = None
stack_ax_scale = 0.05  # for unzooming calculations

surface_fig = None
surface_ax = None
surface_figure_agg = None
surface_xlims = None
surface_ylims = None
surface_unzoom = None
surface_ax_scale = 0.05  # for unzooming calculations
surface_z_color = "viridis"


# plotting functions

def pretty(d, indent=0, print_values=True):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            if print_values:
                print('\t' * (indent + 1) + str(value))


def my_sqrt(val):
    return np.sign(val) * np.sqrt(np.abs(val))


def on_xlims_change(event_ax):
    global single_xlims
    single_xlims = event_ax.get_xlim()
    print("updated xlims: ", single_xlims)


def on_ylims_change(event_ax):
    global single_ylims
    single_ylims = event_ax.get_ylim()
    print("updated ylims: ", single_ylims)


def bkgremove_mouse_coordinates(event):
    x, y = event.xdata, event.ydata
    print(x, y)


def single_update_plot(block_id, x_ordinate, y_ordinates: list, plot_hkls, window):
    global single_figure_agg
    global single_fig, single_ax

    dpi = plt.gcf().get_dpi()
    if single_fig is not None:
        single_height_px = single_fig.get_size_inches()[1] * dpi
    else:
        single_height_px = 382

    single_fig, single_ax = plt.subplots(1, 1)
    single_fig = plt.gcf()
    x_inches = canvas_x / float(dpi)
    y_inches = canvas_y / float(dpi)
    single_fig.set_size_inches(x_inches, y_inches)
    single_fig.set_tight_layout(True)
    plt.margins(x=0)

    filtered_df = dd[block_id]
    x = filtered_df[x_ordinate]

    min_plot = 999999999
    max_plot = -min_plot
    for i, y in enumerate(y_ordinates):
        if y != "None":
            plt.plot(x, filtered_df[y], label=" " + y,
                     color=y_style[i][0], marker=y_style[i][1],
                     linestyle=y_style[i][2], linewidth=y_style[i][3],
                     markersize=float(y_style[i][3]) * 3
                     )
            min_plot = min(min_plot, min(filtered_df[y]))
            max_plot = max(max_plot, max(filtered_df[y]))

    # hkl plotting below     single_height_px

    hkl_x_ordinate_mapping = {"d": "d", "q": "q", "_pd_meas_2theta_scan": "2theta"}
    if plot_hkls:
        y_range = max_plot - min_plot
        hkl_markersize_pt = 6
        hkl_markersize_px = hkl_markersize_pt * 72 / dpi
        num_hkl_rows = len(hkld[block_id]["hkl"]["_pd_phase_id"])
        hkl_tick_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows

        hkl_x_ordinate = hkl_x_ordinate_mapping[x_ordinate]
        for i, phase in enumerate(hkld[block_id]["hkl"]["_pd_phase_id"]):
            hkl_x = hkld[block_id]["hkl"][phase][hkl_x_ordinate]
            hkl_y = [min_plot - 4 * (i + 1) * hkl_tick_spacing] * len(hkld[block_id]["hkl"][phase][hkl_x_ordinate])
            plt.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt)

    plt.legend(frameon=False)  # loc='best')

    # offset for all the mins and maxs
    # sx = bkgremove_ax_scale * (bkgremove_unzoom[1] - bkgremove_unzoom[0])
    # sy = bkgremove_ax_scale * (bkgremove_unzoom[3] - bkgremove_unzoom[2])
    # bkgremove_unzoom = [bkgremove_unzoom[0] - sx, bkgremove_unzoom[1] + sx,
    #                     bkgremove_unzoom[2] - sy, bkgremove_unzoom[3] + sy, ]
    if "intensity" in y_ordinates[0]:
        y_axis_title = "Intensity (arb. units)"
    else:
        y_axis_title = "Counts"

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()

    plt.xlabel(X_AXIS_TITLES[x_ordinate])
    plt.ylabel(y_axis_title)
    plt.title(block_id, loc="left")

    # updates the viewing area of the plot so when a new dataset is  chosen, I can open in it the same viewpoint
    # if single_xlims is not None:
    #     ax.set_xlim(single_xlims[0], single_xlims[1])
    # if single_ylims is not None:
    #     ax.set_ylim(single_ylims[0], single_ylims[1])
    #
    # ax.callbacks.connect('xlim_changed', on_xlims_change)  # gets the xlims
    # ax.callbacks.connect('ylim_changed', on_ylims_change)  # gets the ylims
    # # plt.connect('motion_notify_event', bkgremove_mouse_coordinates)  # gets the mouse coordinates. TODO add these to the status bar

    single_figure_agg = draw_figure_w_toolbar(window["single_plot"].TKCanvas, single_fig,
                                              window["single_matplotlib_controls"].TKCanvas)


def stack_update_plot(x_ordinate, y_ordinate, offset, window):
    global canvas_x, canvas_y, stack_figure_agg
    global stack_fig, stack_ax, data_list

    stack_fig, stack_ax = plt.subplots(1, 1)
    stack_fig = plt.gcf()
    dpi = stack_fig.get_dpi()
    stack_fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    stack_fig.set_tight_layout(True)
    plt.margins(x=0)

    # We need to set the plot limits, they will not autoscale when doing a linecollection
    # going to assume that the y's are well behaved, and that the minimum of the first pattern
    # and the max of the last pattern define the limits of the plot
    x_min = min(dd[x_ordinate])
    x_max = max(dd[x_ordinate])
    y_min = min(dd[data_list[0]][y_ordinate])
    y_max = max(dd[data_list[-1]][y_ordinate]) + (len(data_list) * offset)
    y_range = y_max - y_min
    y_buffer = 0.04 * y_range
    y_max += y_buffer
    y_min -= y_buffer

    stack_ax.set_xlim(x_min, x_max)
    stack_ax.set_ylim(y_min, y_max)

    xs = []
    ys = []
    # put the data into the correct format
    for i in range(len(data_list) - 1, -1, -1):
        pattern = data_list[i]
        xs.append(dd[pattern][x_ordinate])
        ys.append(dd[pattern][y_ordinate] + i * offset)
    xy = [np.column_stack([x, y]) for x, y in zip(xs, ys)]
    line_segments = LineCollection(xy, linestyles='solid', color=mc.TABLEAU_COLORS)
    stack_ax.add_collection(line_segments)

    if "intensity" in y_ordinate:
        y_axis_title = "Intensity (arb. units)"
    else:
        y_axis_title = "Counts"

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()

    plt.xlabel(X_AXIS_TITLES[x_ordinate])
    plt.ylabel(y_axis_title)

    stack_figure_agg = draw_figure_w_toolbar(window["stack_plot"].TKCanvas, stack_fig,
                                             window["stack_matplotlib_controls"].TKCanvas)


def surface_update_plot(x_ordinate, z_ordinate, window):
    global canvas_x, canvas_y, surface_figure_agg
    # try:
    #     bkr = get_bkgremove_from_displayname(displayname)
    # except ValueError:
    #     return None  # stop the execution of this script here

    # if single_figure_agg:
    #     single_figure_agg.get_tk_widget().forget()
    #     plt.close('all')

    global surface_fig, surface_ax, surface_z_color

    surface_fig, surface_ax = plt.subplots(1, 1)
    surface_fig = plt.gcf()
    dpi = surface_fig.get_dpi()
    surface_fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    surface_fig.set_tight_layout(True)
    plt.margins(x=0)

    x = df[x_ordinate].to_numpy()
    z = df[z_ordinate].to_numpy()
    y = pd.factorize(df._pd_block_id)[0]
    # https://stackoverflow.com/a/33943276/36061
    # https://stackoverflow.com/a/38025451/36061
    x = np.unique(x)
    y = np.unique(y)
    xx, yy = np.meshgrid(x, y)
    zz = z.reshape(len(y), len(x))

    plt.pcolormesh(xx, yy, zz, shading='nearest', cmap=surface_z_color)
    plt.colorbar(label=z_ordinate)

    # offset for all the mins and maxs
    # sx = bkgremove_ax_scale * (bkgremove_unzoom[1] - bkgremove_unzoom[0])
    # sy = bkgremove_ax_scale * (bkgremove_unzoom[3] - bkgremove_unzoom[2])
    # bkgremove_unzoom = [bkgremove_unzoom[0] - sx, bkgremove_unzoom[1] + sx,
    #                     bkgremove_unzoom[2] - sy, bkgremove_unzoom[3] + sy, ]
    y_axis_title = "Pattern number"

    if x_ordinate in ["d", "_pd_proc_d_spacing"]:
        plt.gca().invert_xaxis()

    plt.xlabel(X_AXIS_TITLES[x_ordinate])
    plt.ylabel(y_axis_title)
    #
    # plt.plot(40, 15, marker="|", markersize=6)
    #
    # pretty(hkld)
    # hkl_x_ordinate_mapping = {"d": "d", "q": "q", "_pd_meas_2theta_scan": "2theta"}
    # hkl_x_ordinate = hkl_x_ordinate_mapping[x_ordinate]



    # if plot_hkls:
    #     y_range = max_plot - min_plot
    #     hkl_markersize_pt = 6
    #     hkl_markersize_px = hkl_markersize_pt * 72 / dpi
    #     num_hkl_rows = len(hkld[block_id]["hkl"]["_pd_phase_id"])
    #     hkl_tick_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows
    #
    #
    #     for i, phase in enumerate(hkld[block_id]["hkl"]["_pd_phase_id"]):
    #         hkl_x = hkld[block_id]["hkl"][phase][hkl_x_ordinate]
    #         hkl_y = [min_plot - 4 * (i + 1) * hkl_tick_spacing] * len(hkld[block_id]["hkl"][phase][hkl_x_ordinate])
    #         plt.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt)

    # updates the viewing area of the plot so when a new dataset is  chosen, I can open in it the same viewpoint
    # if single_xlims is not None:
    #     ax.set_xlim(single_xlims[0], single_xlims[1])
    # if single_ylims is not None:
    #     ax.set_ylim(single_ylims[0], single_ylims[1])
    #
    # ax.callbacks.connect('xlim_changed', on_xlims_change)  # gets the xlims
    # ax.callbacks.connect('ylim_changed', on_ylims_change)  # gets the ylims
    # # plt.connect('motion_notify_event', bkgremove_mouse_coordinates)  # gets the mouse coordinates. TODO add these to the status bar

    surface_figure_agg = draw_figure_w_toolbar(window["surface_plot"].TKCanvas, surface_fig,
                                               window["surface_matplotlib_controls"].TKCanvas)


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
# https://github.com/PySimpleGUI/PySimpleGUI/issues/3989#issuecomment-794005240
def draw_figure_w_toolbar(canvas, figure, canvas_toolbar):
    start_time = time.time()
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

    finish_time = time.time()

    print(f"draw_figure_w_toolbar took {finish_time - start_time} units of time.")
    return figure_canvas_agg


# https://github.com/PySimpleGUI/PySimpleGUI/blob/master/DemoPrograms/Demo_Matplotlib_Embedded_Toolbar.py
class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)


def y_ordinate_styling_popup(window_title, color_default, marker_styles_default, line_style_default, size_default, key, window):
    layout = [
        [sg.Text(f"Here's the \nuser-defined \npopup for {key}!!!")],
        [sg.Combo(LINE_MARKER_COLORS, default_value=color_default, key=key + "-popup-color"),
         sg.Combo(MARKER_STYLES, default_value=marker_styles_default, key=key + "-popup-markerstyle"),
         sg.Combo(LINE_STYLES, default_value=line_style_default, key=key + "-popup-linestyle"),
         sg.Combo(LINE_MARKER_SIZE, default_value=size_default, key=key + "-popup-size")],
        [sg.Button("Ok", key=key + "-popup-ok", enable_events=True),
         sg.Button("Cancel", key=key + "-popup-cancel", enable_events=True)]
    ]
    win = sg.Window(window_title, layout, modal=True, grab_anywhere=True, enable_close_attempted_event=True)
    event, values = win.read()
    win.close()
    window.write_event_value(event, values)


def z_ordinate_styling_popup(window_title, color_default, key, window):
    layout = [
        [sg.Text(f"Here's the \nuser-defined \npopup for {key}!!!")],
        [sg.Combo(SURFACE_COLOR_MAPS, default_value=color_default, key=key + "-popup-color")],
        [sg.Button("Ok", key=key + "-popup-ok", enable_events=True),
         sg.Button("Cancel", key=key + "-popup-cancel", enable_events=True)]
    ]
    win = sg.Window(window_title, layout, modal=True, grab_anywhere=True, enable_close_attempted_event=True)
    event, values = win.read()
    win.close()
    window.write_event_value(event, values)


######################################################################################################
#######################################################################################################
######################################################################################################

def cif_dataframe_to_dict(df, patterns=None, columns=None):
    data_dict = {}

    if patterns is None:
        patterns = [str(val) for val in df["_pd_block_id"].unique()]
    if columns is None:
        columns = [value for value in list(df.columns) if value != "_pd_block_id"]

    # to get a unique numerical index for each pattern
    indexes = [i for i in range(len(patterns))]
    # To store a concatenated array of column values across all patterns
    cum_columns = [None] * (len(columns) + 1)

    for i, pattern in enumerate(patterns):
        pattern_dict = {}
        filtered_df = df[df["_pd_block_id"] == pattern]
        for j, column in enumerate(columns):
            nparr = filtered_df[column].to_numpy()
            pattern_dict[column] = nparr
            if cum_columns[j] is None:
                cum_columns[j] = nparr
            else:
                cum_columns[j] = np.concatenate((cum_columns[j], nparr), axis=None)
        index = np.asarray([indexes[i]] * len(filtered_df))
        if cum_columns[-1] is None:
            cum_columns[-1] = index
        else:
            cum_columns[-1] = np.concatenate((cum_columns[-1], index), axis=None)
        data_dict[pattern] = pattern_dict

    for col_name, col_vals in zip(columns + ["index"], cum_columns):
        data_dict[col_name] = col_vals
    return data_dict


def hkl_dataframe_to_dict(df, patterns=None, columns=None):
    data_dict = {}

    if patterns is None:
        patterns = [str(val) for val in df["_pd_block_id"].unique()]
    if columns is None:
        columns = [value for value in list(df.columns) if value != "_pd_block_id"]

    for pattern in patterns:
        pattern_dict = {}
        pattern_df = df[df["_pd_block_id"] == pattern]
        phases = [str(val) for val in df["_pd_refln_phase_id"].unique()]
        pattern_dict["_pd_phase_id"] = phases
        for phase in phases:
            phase_dict = {}
            phase_df = pattern_df[pattern_df["_pd_refln_phase_id"].astype(str) == phase]
            phase_dict["hover_text"] = phase_df['hover_text'].to_numpy()
            phase_dict["d"] = phase_df['_refln_d_spacing'].to_numpy()
            phase_dict["q"] = phase_df['q'].to_numpy()
            phase_dict["2theta"] = phase_df['2theta'].to_numpy()
            pattern_dict[phase] = phase_dict
        data_dict[pattern] = {"hkl": pattern_dict}

    return data_dict


# This will eventually be set through the user uploading a copy of their CIF.
# For now, I just want to get it running.
df = pd.read_table("../../data/diff_data.txt")

hkl_df = pd.read_table(r"../../data/hkl_data.txt")
hkl_df["q"] = 2 * np.pi / hkl_df["_refln_d_spacing"]
hkl_df["2theta"] = 2 * np.arcsin(hkl_df["_diffrn_radiation_wavelength"] / (2 * hkl_df["_refln_d_spacing"])) * 180. / np.pi
hkl_df['hover_text'] = hkl_df['_refln_index_h'].astype(str) + " " + hkl_df['_refln_index_k'].astype(str) + " " + hkl_df["_refln_index_l"].astype(str)

# this bit would normally be done in the cif reading ot
df["d"] = df["_diffrn_radiation_wavelength"] / (2 * np.sin(df["_pd_meas_2theta_scan"] * np.pi / 360.))
df["q"] = 2 * np.pi / df["d"]
df["diff"] = df["_pd_meas_intensity_total"] - df["_pd_calc_intensity_total"]
df["diff"] = df["diff"] - max(df["diff"])

hkld = hkl_dataframe_to_dict(hkl_df)
dd = cif_dataframe_to_dict(df)

# merge hkld into dd


# todo: this will have to be a dictionary that allows lookup by data name, in case it changes per pattern
wavelength = 0.8257653  # just for argument's sake
if wavelength is not None:
    _lam = f"(\u03BB = {str(wavelength)} \u212b)"
else:
    _lam = ""

data_list = [str(val) for val in df["_pd_block_id"].unique()]

# these lists contain all the possible x and y ordinate data items that I want to worry about in this program
# the last few entries in each list correspond to values that could potentially be calc'd from the given
# information, but were not presented in the CIF.
COMPLETE_X_LIST = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
                   "_pd_meas_position", "_pd_proc_energy_incident", "_pd_proc_wavelength",
                   "_pd_proc_d_spacing", "_pd_proc_recip_len_Q", "d", "q"]
COMPLETE_Y_LIST = ["_pd_meas_counts_total", "_pd_meas_intensity_total", "_pd_proc_intensity_total",
                   "_pd_proc_intensity_net", "_pd_calc_intensity_net", "_pd_calc_intensity_total",
                   "_pd_meas_counts_background", "_pd_meas_counts_container", "_pd_meas_intensity_background",
                   "_pd_meas_intensity_container", "_pd_proc_intensity_bkg_calc", "_pd_proc_intensity_bkg_fix", "diff"]

X_AXIS_TITLES = {"_pd_meas_2theta_scan": f"\u00B0 2\u03b8 {_lam}",
                 "_pd_proc_2theta_corrected": f"\u00B0 2\u03b8 corrected {_lam}",
                 "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                 "_pd_meas_position": "Position (mm)",
                 "_pd_proc_energy_incident": "Incident energy (eV)",
                 "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                 "_pd_proc_d_spacing": "d spacing (\u212b)",
                 "_pd_proc_recip_len_Q": "q (1/\u212b)",
                 "d": "d spacing (\u212b)",
                 "q": "q (1/\u212b)"}

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

# LINE_MARKER_COLORS = list(mc.CSS4_COLORS.keys())
# from here: https://matplotlib.org/stable/gallery/color/named_colors.html
_by_hsv = sorted((tuple(mc.rgb_to_hsv(mc.to_rgb(color))), name) for name, color in mc.CSS4_COLORS.items())
LINE_MARKER_COLORS = [name for hsv, name in _by_hsv]
MARKER_STYLES = [None, ".", "o", "s", "*", "+", "x", "D"]
LINE_STYLES = ["solid", "None", "dashed", "dashdot", "dotted"]
LINE_MARKER_SIZE = [str(s) for s in range(1, 30)]

SURFACE_COLOR_MAPS_SOURCE = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

SURFACE_COLOR_MAPS = []
for c in SURFACE_COLOR_MAPS_SOURCE:
    SURFACE_COLOR_MAPS.append(c)
    SURFACE_COLOR_MAPS.append(c + "_r")


def make_list_for_ordinate_dropdown(complete_list, possible_list):
    used_list = []
    for t in complete_list:
        if t in possible_list:
            used_list.append(t)
    used_list.append("None")
    return used_list


x_list = make_list_for_ordinate_dropdown(COMPLETE_X_LIST, list(df.columns))
y_list = make_list_for_ordinate_dropdown(COMPLETE_Y_LIST, list(df.columns))

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
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True)]


def label_dropdown_button_row(label, button_text, values, default, key):
    return [sg.T(label),
            sg.Combo(values=values, default_value=default, enable_events=True, key=key, readonly=True),
            sg.Button(button_text=button_text, key=key + "_button")]


#################################################################################################################
#
# --- single tab
#
#################################################################################################################

layout_single_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="single_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Sizer(v_pixels=60), sg.Canvas(key="single_matplotlib_controls")]
    ]

layout_single_data_chooser = \
    [[
        sg.Combo(values=data_list,  # ["Load some files to start!"],
                 # size=(action_column_width, 10),
                 enable_events=True,
                 key="single_data_chooser",
                 readonly=True),
        sg.Push(),
    ]]

layout_single_plot_control = \
    [
        label_dropdown_row("X axis:  ", x_list, x_list[0], "single_x_ordinate"),
        label_dropdown_button_row("Y axis 1:", "Options", y_list, y_list[0], "single_y1_ordinate"),
        label_dropdown_button_row("Y axis 2:", "Options", y_list, y_list[1], "single_y2_ordinate"),
        label_dropdown_button_row("Y axis 3:", "Options", y_list, y_list[2], "single_y3_ordinate"),
        label_dropdown_button_row("Y axis 4:", "Options", y_list, y_list[3], "single_y4_ordinate"),
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key="single_hkl_checkbox"),
         sg.Radio("Above", "hkl", enable_events=True, key="single_hkl_checkbox_above"),
         sg.Radio("Below", "hkl", default=True, enable_events=True, key="single_hkl_checkbox_below")],
        [sg.Checkbox("Show cumulative chi\u00B2", enable_events=True, key="single_chi2_checkbox")],
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="single_normalise_intensity_checkbox")],
        # [sg.Checkbox("Show error bars", enable_events=True, key="single_error_bars_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "single_x_scale_radio", default=True, enable_events=True, key="single_x_scale_linear"),
         sg.Radio("Sqrt", "single_x_scale_radio", enable_events=True, key="single_x_scale_sqrt"),
         sg.Radio("Log", "single_x_scale_radio", enable_events=True, key="single_x_scale_log")],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "single_y_scale_radio", default=True, enable_events=True, key="single_y_scale_linear"),
         sg.Radio("Sqrt", "single_y_scale_radio", enable_events=True, key="single_y_scale_sqrt"),
         sg.Radio("Log", "single_y_scale_radio", enable_events=True, key="single_y_scale_log")]
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

layout_stack_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="stack_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Canvas(key="stack_matplotlib_controls")]
    ]

layout_stack_plot_control = \
    [
        label_dropdown_row("X axis:", x_list, x_list[0], "stack_x_ordinate"),
        label_dropdown_row("Y axis:", y_list, y_list[0], "stack_y_ordinate"),
        # label_dropdown_button_row("Y axis:", "Options", y_list, y_list[0], "stack_y_ordinate"),
        [sg.T("Offset:"), sg.Input(default_text=100, size=(6, 1), enable_events=False, key="stack_offset_input"),
         sg.Button('Submit_offset', visible=False, bind_return_key=True, key="stack_offset_value", enable_events=True)],
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key="stack_hkl_checkbox"),
         sg.Radio("Above", "hkl", enable_events=True, key="stack_hkl_checkbox_above"),
         sg.Radio("Below", "hkl", default=True, enable_events=True, key="stack_hkl_checkbox_below")],
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="stack_normalise_intensity_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "stack_x_scale_radio", default=True, enable_events=True, key="stack_x_scale_linear"),
         sg.Radio("Sqrt", "stack_x_scale_radio", enable_events=True, key="stack_x_scale_sqrt"),
         sg.Radio("Log", "stack_x_scale_radio", enable_events=True, key="stack_x_scale_log")],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "stack_y_scale_radio", default=True, enable_events=True, key="stack_y_scale_linear"),
         sg.Radio("Sqrt", "stack_y_scale_radio", enable_events=True, key="stack_y_scale_sqrt"),
         sg.Radio("Log", "stack_y_scale_radio", enable_events=True, key="stack_y_scale_log")]
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

#################################################################################################################
#
# --- surface tab
#
#################################################################################################################

layout_surface_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="surface_plot", expand_x=True, expand_y=True)]], pad=(0, 0), expand_x=True, expand_y=True)],
        [sg.Canvas(key="surface_matplotlib_controls")]
    ]

layout_surface_plot_control = \
    [
        label_dropdown_row("X axis:", x_list, x_list[0], "surface_x_ordinate"),
        label_dropdown_row("Y axis:", ["Pattern number"], "Pattern number", "surface_y_ordinate"),
        label_dropdown_button_row("Z axis:", "Options", y_list, y_list[0], "surface_z_ordinate"),
        # --
        [sg.T("")],
        [sg.Checkbox("Show HKL ticks", enable_events=True, key="surface_hkl_checkbox"),
         sg.Radio("Above", "hkl", enable_events=True, key="surface_hkl_checkbox_above"),
         sg.Radio("Below", "hkl", default=True, enable_events=True, key="surface_hkl_checkbox_below")],
        # [sg.Checkbox("Normalise intensity", enable_events=True, key="surface_normalise_intensity_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "surface_x_scale_radio", default=True, enable_events=True, key="surface_x_scale_linear"),
         sg.Radio("Sqrt", "surface_x_scale_radio", enable_events=True, key="surface_x_scale_sqrt"),
         sg.Radio("Log", "surface_x_scale_radio", enable_events=True, key="surface_x_scale_log")],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "surface_y_scale_radio", default=True, enable_events=True, key="surface_y_scale_linear"),
         sg.Radio("Sqrt", "surface_y_scale_radio", enable_events=True, key="surface_y_scale_sqrt"),
         sg.Radio("Log", "surface_y_scale_radio", enable_events=True, key="surface_y_scale_log")],
        [sg.Text("Z scale:"),
         sg.Radio("Linear", "surface_z_scale_radio", default=True, enable_events=True, key="surface_z_scale_linear"),
         sg.Radio("Sqrt", "surface_z_scale_radio", enable_events=True, key="surface_z_scale_sqrt"),
         sg.Radio("Log", "surface_z_scale_radio", enable_events=True, key="surface_z_scale_log")]
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

window = sg.Window("pdCIFplotter", layout, finalize=True, use_ttk_buttons=True, resizable=True)  # , ttk_theme=sg.THEME_WINNATIVE)


# window.bind('<Configure>', "resize")
# window.maximize()

# window["single_right_column"].expand(expand_x=True, expand_y=True)
# window["single_data_chooser_frame"].expand(expand_x=False, expand_y=True, expand_row=True)
# window["single_plot_controls_frame"].expand(expand_x=True, expand_y=True)
# window["stack_plot_controls_frame"].expand(expand_x=True, expand_y=True)


# # set all the buttons to disabled before I have data to do things to.
# window["bkgremove_remove_selected_files"].update(disabled=True)
# window["bkgremove_remove_all_files"].update(disabled=True)
# window["bkgremove_trim_current"].update(disabled=True)
# window["bkgremove_trim_selected"].update(disabled=True)
# window["bkgremove_fit_current"].update(disabled=True)
# window["bkgremove_fit_selected"].update(disabled=True)
# window["bkgremove_reset_cheb_coeffs"].update(disabled=True)
# window["bkgremove_export_data"].update(disabled=True)

def parse_cif_file(files_str):
    print(f"I still need to do this so I can open {files_str}.")


def populate_all_the_lists_for_the_plot_controls():
    print("do the thing to make all the dropdowns have the correct values")


while True:
    event, values = window.read()

    # print(f"{event=}")
    # print(f"{values=}")

    theValue = ""
    try:
        theValue = values[event]
    except:
        theValue = "__none__"
    print("-----------------\n", event, ":", theValue, " --- ", values, "\n-----------------")

    #     newfilelist = bkgremove_list_to_displaynames()
    if event is None:
        break

    # ----------
    # loading files
    # ----------
    elif event == "file_string":
        files_str = values['file_string']
        if not files_str == "":
            parse_cif_file(files_str)
            populate_all_the_lists_for_the_plot_controls()
            # reset the figures
            single_figure_agg = None
            stack_figure_agg = None
            surface_figure_agg = None
            # update the data-dropdown with the unique names
            # window["single_data_chooser"].update(values=bkgremove_list_to_displaynames())
        window["file_string"].update(value=[])
        window["file_string_name"].update(value=values["file_string"])
        # now enable all the buttons
        # window["bkgremove_remove_selected_files"].update(disabled=False)
        # window["bkgremove_remove_all_files"].update(disabled=False)
        # window["bkgremove_trim_current"].update(disabled=False)
        # window["bkgremove_trim_selected"].update(disabled=False)
        # window["bkgremove_fit_current"].update(disabled=False)
        # window["bkgremove_fit_selected"].update(disabled=False)
        # window["bkgremove_reset_cheb_coeffs"].update(disabled=False)

    # --------------------------------------------------------------------------------------
    #
    #  single window things
    #
    # --------------------------------------------------------------------------------------

    elif event in ["single_data_chooser", "single_x_ordinate", "single_y1_ordinate", "single_y2_ordinate",
                   "single_y3_ordinate", "single_y4_ordinate", "single_hkl_checkbox"]:
        # I'm choosing a new dataset to plot, or altering what I'm plotting
        plot_block_id = values["single_data_chooser"]
        x_ordinate = values["single_x_ordinate"]
        y1_ordinate = values["single_y1_ordinate"]
        y2_ordinate = values["single_y2_ordinate"]
        y3_ordinate = values["single_y3_ordinate"]
        y4_ordinate = values["single_y4_ordinate"]
        plot_hkls = values["single_hkl_checkbox"]
        try:
            single_update_plot(plot_block_id, x_ordinate, [y1_ordinate, y2_ordinate, y3_ordinate, y4_ordinate], plot_hkls, window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    elif event == "single_y1_ordinate_button":
        y_ordinate_styling_popup("Y1 styling", y_style[0][0], y_style[0][1], y_style[0][2], y_style[0][3], "y1-popupkey", window)
    elif event == "y1-popupkey-popup-ok":
        # update the style calues
        y_style[0] = [values["y1-popupkey-popup-ok"]['y1-popupkey-popup-color'],
                      values["y1-popupkey-popup-ok"]['y1-popupkey-popup-markerstyle'],
                      values["y1-popupkey-popup-ok"]['y1-popupkey-popup-linestyle'],
                      values["y1-popupkey-popup-ok"]['y1-popupkey-popup-size']]
        # replot the plot
        try:
            single_update_plot(values["single_data_chooser"], values["single_x_ordinate"],
                               [values["single_y1_ordinate"], values["single_y2_ordinate"], values["single_y3_ordinate"], values["single_y4_ordinate"]],
                               values["single_hkl_checkbox"], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    elif event == "single_y2_ordinate_button":
        y_ordinate_styling_popup("y2 styling", y_style[1][0], y_style[1][1], y_style[1][2], y_style[1][3], "y2-popupkey", window)
    elif event == "y2-popupkey-popup-ok":
        # update the style calues
        y_style[1] = [values["y2-popupkey-popup-ok"]['y2-popupkey-popup-color'],
                      values["y2-popupkey-popup-ok"]['y2-popupkey-popup-markerstyle'],
                      values["y2-popupkey-popup-ok"]['y2-popupkey-popup-linestyle'],
                      values["y2-popupkey-popup-ok"]['y2-popupkey-popup-size']]
        # replot the plot
        try:
            single_update_plot(values["single_data_chooser"], values["single_x_ordinate"],
                               [values["single_y1_ordinate"], values["single_y2_ordinate"], values["single_y3_ordinate"], values["single_y4_ordinate"]],
                               values["single_hkl_checkbox"], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    elif event == "single_y3_ordinate_button":
        y_ordinate_styling_popup("y3 styling", y_style[2][0], y_style[2][1], y_style[2][2], y_style[2][3], "y3-popupkey", window)
    elif event == "y3-popupkey-popup-ok":
        # update the style calues
        y_style[2] = [values["y3-popupkey-popup-ok"]['y3-popupkey-popup-color'],
                      values["y3-popupkey-popup-ok"]['y3-popupkey-popup-markerstyle'],
                      values["y3-popupkey-popup-ok"]['y3-popupkey-popup-linestyle'],
                      values["y3-popupkey-popup-ok"]['y3-popupkey-popup-size']]
        # replot the plot
        try:
            single_update_plot(values["single_data_chooser"], values["single_x_ordinate"],
                               [values["single_y1_ordinate"], values["single_y2_ordinate"], values["single_y3_ordinate"], values["single_y4_ordinate"]],
                               values["single_hkl_checkbox"], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    elif event == "single_y4_ordinate_button":
        y_ordinate_styling_popup("y4 styling", y_style[3][0], y_style[3][1], y_style[3][2], y_style[3][3], "y4-popupkey", window)
    elif event == "y4-popupkey-popup-ok":
        # update the style calues
        y_style[3] = [values["y4-popupkey-popup-ok"]['y4-popupkey-popup-color'],
                      values["y4-popupkey-popup-ok"]['y4-popupkey-popup-markerstyle'],
                      values["y4-popupkey-popup-ok"]['y4-popupkey-popup-linestyle'],
                      values["y4-popupkey-popup-ok"]['y4-popupkey-popup-size']]
        # replot the plot
        try:
            single_update_plot(values["single_data_chooser"], values["single_x_ordinate"],
                               [values["single_y1_ordinate"], values["single_y2_ordinate"], values["single_y3_ordinate"], values["single_y4_ordinate"]],
                               values["single_hkl_checkbox"], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    # --------------------------------------------------------------------------------------
    #  stack window things
    # --------------------------------------------------------------------------------------
    elif (event == "tab-change" and values[event] == "stack_tab" and stack_figure_agg is None) or \
            event in ["stack_x_ordinate", "stack_y_ordinate", "stack_offset_input", "stack_offset_value"]:
        x_ordinate = values["stack_x_ordinate"]
        y_ordinate = values["stack_y_ordinate"]
        offset = float(values["stack_offset_input"])
        try:
            stack_update_plot(x_ordinate, y_ordinate, offset, window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    # --------------------------------------------------------------------------------------
    #  surface window things
    # --------------------------------------------------------------------------------------
    elif (event == "tab-change" and values[event] == "surface_tab" and surface_figure_agg is None) or \
            event in ["surface_x_ordinate", "surface_z_ordinate"]:
        x_ordinate = values["surface_x_ordinate"]
        z_ordinate = values["surface_z_ordinate"]
        try:
            surface_update_plot(x_ordinate, z_ordinate, window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)

    elif event == "surface_z_ordinate_button":
        z_ordinate_styling_popup("Surface Z colour scale", surface_z_color, "surface_z_color", window)
    elif event == "surface_z_color-popup-ok":
        surface_z_color = values["surface_z_color-popup-ok"]['surface_z_color-popup-color']
        try:
            surface_update_plot(values["surface_x_ordinate"], values["surface_z_ordinate"], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)
