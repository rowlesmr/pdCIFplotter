# -*- coding: utf-8 -*-
"""
Created on Sun Jul  4 20:56:13 2021

@author: 184277J
"""

import PySimpleGUIQt as sg
import numpy as np
import pandas as pd
import ntpath
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib._color_data as mcd  # a lot of colour choices in here to use

# Potential themes that work for me.  #reddit is the only one that doesn't jitter...  ?
MY_THEMES = ["Default1", "GrayGrayGray", "Reddit", "SystemDefault1", "SystemDefaultForReal"]
sg.theme(MY_THEMES[2])

# import traceback
# import sys


# global parameters
action_column_width = 30
canvas_x = 1200
canvas_y = 700
fig = None
ax = None

bkgremove_list = []  # this is a list of BkgRemove objects corresponding to the ones I've opened in the GUI
single_figure_agg = None
single_xlims = None
single_ylims = None
single_unzoom = None
single_ax_scale = 0.05  # for unzooming calculations


# plotting functions

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


def single_update_plot(block_id, x_ordinate, y_ordinates: list, window):
    global single_list, canvas_x, canvas_y, single_figure_agg
    # try:
    #     bkr = get_bkgremove_from_displayname(displayname)
    # except ValueError:
    #     return None  # stop the execution of this script here

    # if single_figure_agg:
    #     single_figure_agg.get_tk_widget().forget()
    #     plt.close('all')

    global fig, ax

    fig, ax = plt.subplots(1, 1)
    fig = plt.gcf()
    dpi = fig.get_dpi()
    fig.set_size_inches(canvas_x / float(dpi), canvas_y / float(dpi))
    plt.margins(x=0)

    # set up the plots

    stack = 0
    surface = 1
    if stack:
        offset = 100
        for i in range(len(data_list) - 1, -1, -1):
            pattern = data_list[i]
            zorder = 1 + (len(data_list) - i) / len(data_list)
            filtered_df = df[df["_pd_block_id"] == pattern]
            x = filtered_df[x_ordinate]
            y = filtered_df[y_ordinates[0]] + i * offset
            plt.plot(x, y, label=pattern, zorder=zorder)
            plt.fill_between(x, y, color="white", zorder=zorder)

    elif surface:
        x = df[x_ordinate].to_numpy()
        # x = df["d"].to_numpy()
        z = df[y_ordinates[0]].to_numpy()
        y = pd.factorize(df._pd_block_id)[0]
        # https://stackoverflow.com/a/33943276/36061
        # https://stackoverflow.com/a/38025451/36061
        x = np.unique(x)
        y = np.unique(y)
        X, Y = np.meshgrid(x, y)

        Z = z.reshape(len(y), len(x))

        plt.pcolormesh(X, Y, Z, shading='nearest')
        plt.colorbar(label="label")

    else:
        filtered_df = df[df["_pd_block_id"] == block_id]
        x = filtered_df[x_ordinate]

        for y in y_ordinates:
            if y != "None":
                plt.plot(x, filtered_df[y], label=" " + y)  # , color="black", linewidth=0.75)

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

    plt.xlabel(x_axis_titles[x_ordinate])
    plt.ylabel(y_axis_title)
    plt.title(block_id, loc="left")
    plt.legend(frameon=False)  # loc='best')

    # updates the viewing area of the plot so when a new dataset is  chosen, I can open in it the same viewpoint
    # if single_xlims is not None:
    #     ax.set_xlim(single_xlims[0], single_xlims[1])
    # if single_ylims is not None:
    #     ax.set_ylim(single_ylims[0], single_ylims[1])
    #
    # ax.callbacks.connect('xlim_changed', on_xlims_change)  # gets the xlims
    # ax.callbacks.connect('ylim_changed', on_ylims_change)  # gets the ylims
    # # plt.connect('motion_notify_event', bkgremove_mouse_coordinates)  # gets the mouse coordinates. TODO add these to the status bar

    single_figure_agg = draw_figure_w_toolbar(window["single_plot"].TKCanvas, fig,
                                              window["single_matplotlib_controls"].TKCanvas)


def bkgremove_unzoom_plot():
    global single_unzoom, ax
    ax.set_xlim(single_unzoom[0], single_unzoom[1])
    ax.set_ylim(single_unzoom[2], single_unzoom[3])


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


def y_ordinate_styling_popup(key, window):
    layout = [
        [sg.Text(f"Here's the \nuser-defined \npopup for {key}!!!")],
        [sg.Combo(["First", "Second", "Third"], default_value="First", key=key + "-popup-lineorder"),
         sg.Combo(["Red", "Green", "Blue"], default_value="Red", key=key + "-popup-linecolour"),
         sg.Combo(["+", "o", "X", "-"], default_value="+", key=key + "-popup-markerstyle")],
        [sg.Button("OK", key=key + "-popup-ok", enable_events=True),
         sg.Button("CANCEL", key=key + "-popup-cancel", enable_events=True)]
    ]
    win = sg.Window(f"My {key} Popup", layout, modal=True, grab_anywhere=True, enable_close_attempted_event=True)

    event, values = win.read()
    win.close()
    window.write_event_value(event, values)


######################################################################################################
#######################################################################################################
######################################################################################################

# This will eventually be set through the user uploading a copy of their CIF.
# For now, I just want to get it running.
df = pd.read_table("../../data/diff_data.txt")
# this bit would normally be done in the cif reading ot
df["d"] = df["_diffrn_radiation_wavelength"] / (2 * np.sin(df["_pd_meas_2theta_scan"] * np.pi / 360.))
df["q"] = 2 * np.pi / df["d"]
df["diff"] = df["_pd_meas_intensity_total"] - df["_pd_calc_intensity_total"]
df["diff"] = df["diff"] - max(df["diff"])

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
complete_x_list = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
                   "_pd_meas_position", "_pd_proc_energy_incident", "_pd_proc_wavelength",
                   "_pd_proc_d_spacing", "_pd_proc_recip_len_Q", "d", "q"]
complete_y_list = ["_pd_meas_counts_total", "_pd_meas_intensity_total", "_pd_proc_intensity_total",
                   "_pd_proc_intensity_net", "_pd_calc_intensity_net", "_pd_calc_intensity_total",
                   "_pd_meas_counts_background", "_pd_meas_counts_container", "_pd_meas_intensity_background",
                   "_pd_meas_intensity_container", "_pd_proc_intensity_bkg_calc", "_pd_proc_intensity_bkg_fix", "diff"]

x_axis_titles = {"_pd_meas_2theta_scan": f"\u00B0 2\u03b8 {_lam}",
                 "_pd_proc_2theta_corrected": f"\u00B0 2\u03b8 corrected {_lam}",
                 "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                 "_pd_meas_position": "Position (mm)",
                 "_pd_proc_energy_incident": "Incident energy (eV)",
                 "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                 "_pd_proc_d_spacing": "d spacing (\u212b)",
                 "_pd_proc_recip_len_Q": "q (1/\u212b)",
                 "d": "d spacing (\u212b)",
                 "q": "q (1/\u212b)"}

complete_xy_plaintext_dict = {"_pd_meas_2theta_scan": "\u00B0 2\u03b8 measured",
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


def make_list_for_ordinate_dropdown(complete_list, possible_list):
    used_list = []
    for t in complete_list:
        if t in possible_list:
            used_list.append(t)
    used_list.append("None")
    return used_list


x_list = make_list_for_ordinate_dropdown(complete_x_list, list(df.columns))
y_list = make_list_for_ordinate_dropdown(complete_y_list, list(df.columns))

# single
# --------------------------------------- #
# |                      |              | #
# |                      | data_chooser | #
# |                      |              | #
# |                      |--------------| #
# |                      | plot_control | #
# |         plot         |              | #
# |                      |              | #
# |                      |              | #
# |                      |              | #
# |                      |              | #
# |                      |              | #
# |----------------------|              | #
# |    file_chooser      |              | #
# --------------------------------------- #


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
# --- Background removal tab
#
#################################################################################################################

layout_single_left = \
    [
        [sg.Column(layout=[[sg.Canvas(size=(canvas_x, canvas_y), key="single_plot")]], pad=(0, 0))],
        [sg.Canvas(key="single_matplotlib_controls")]
    ]

layout_single_data_chooser = \
    [[
        sg.Combo(values=data_list,  # ["Load some files to start!"],
                 # size=(action_column_width, 10),
                 enable_events=True,
                 key="single_data_chooser",
                 readonly=True),
        sg.Stretch(),
        sg.In(key='single_files_string', visible=False, enable_events=True),
        sg.FilesBrowse(button_text="Load file",
                       target='single_files_string',
                       key="single_load_files",
                       file_types=(('CIF Files', '*.cif'),
                                   ('State Files', '*.state'),
                                   ('ALL Files', '*.*')),
                       enable_events=True)  # may need to implement OneLineProgressMeter one loading and parsing CIF
    ]]

layout_single_plot_control = \
    [
        label_dropdown_row("X axis:", x_list, x_list[0], "single_x_ordinate"),
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
        [sg.Checkbox("Normalise intensity", enable_events=True, key="single_normalise_intensity_checkbox")],
        [sg.Checkbox("Show error bars", enable_events=True, key="single_error_bars_checkbox")],
        # --
        [sg.T("")],
        [sg.Text("X scale:"),
         sg.Radio("Linear", "x_scale_radio", default=True, enable_events=True, key="single_x_scale_linear"),
         sg.Radio("Sqrt", "x_scale_radio", enable_events=True, key="single_x_scale_sqrt"),
         sg.Radio("Log", "x_scale_radio", enable_events=True, key="single_x_scale_log")],
        [sg.Text("Y scale:"),
         sg.Radio("Linear", "y_scale_radio", default=True, enable_events=True, key="single_y_scale_linear"),
         sg.Radio("Sqrt", "y_scale_radio", enable_events=True, key="single_y_scale_sqrt"),
         sg.Radio("Log", "y_scale_radio", enable_events=True, key="single_y_scale_log")],
        # [sg.VStretch()]
    ]

layout_single_right = \
    [
        [sg.Frame("Data", layout_single_data_chooser, key="single_data_chooser_frame")],
        [sg.Frame("Plot controls", layout_single_plot_control, key="single_plot_controls_frame")]
    ]

layout_single = \
    [
        [
            sg.Column(layout_single_left, pad=(0, 0)),
            sg.VerticalSeparator(),
            sg.Column(layout_single_right, key="single_right_column", pad=(0, 0))
        ]
    ]

#################################################################################################################
#
# --- Window layout, generation, and expansion
#
#################################################################################################################

layout = \
    [[
        sg.TabGroup(
            [[
                sg.Tab("Single", layout_single, key="single_tab"),
                # sg.Tab("Stack", layout_single, key="pksearch_tab"),
                # sg.Tab("Surface", layout_single, key="phasefind_tab")
            ]],
            tab_location='topleft',
            key='main_window',
            enable_events=True)
    ]]

window = sg.Window("pdCIFplotter", layout, finalize=True)#, use_ttk_buttons=True)  # , ttk_theme=sg.THEME_WINNATIVE)

window.finalize()
#window["single_right_column"].expand(expand_x=True, expand_y=True)
#window["single_data_chooser_frame"].expand(expand_x=False, expand_y=True)
#window["single_plot_controls_frame"].expand(expand_x=True, expand_y=True)


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

    print("-----------------\n", event, "--", values, "\n-----------------")

    #     newfilelist = bkgremove_list_to_displaynames()
    if event is None:
        break

    # --------------------------------------------------------------------------------------
    #
    #  single window things
    #
    # --------------------------------------------------------------------------------------

    # ----------
    # loading files into single
    # ----------
    elif event == "single_files_string":
        files_str = values['single_files_string']
        if not files_str == "":
            parse_cif_file(files_str)
            populate_all_the_lists_for_the_plot_controls()
            # update the data-dropdown with the unique names
            window["single_data_chooser"].update(values=bkgremove_list_to_displaynames())
        window["single_files_string"].update(value=[])
        # now enable all the buttons
        # window["bkgremove_remove_selected_files"].update(disabled=False)
        # window["bkgremove_remove_all_files"].update(disabled=False)
        # window["bkgremove_trim_current"].update(disabled=False)
        # window["bkgremove_trim_selected"].update(disabled=False)
        # window["bkgremove_fit_current"].update(disabled=False)
        # window["bkgremove_fit_selected"].update(disabled=False)
        # window["bkgremove_reset_cheb_coeffs"].update(disabled=False)

    elif event in ["single_data_chooser", "single_x_ordinate", "single_y1_ordinate", "single_y2_ordinate",
                   "single_y3_ordinate", "single_y4_ordinate"]:
        # I'm choosing a new dataset to plot, or altering what I'm plotting
        plot_block_id = values["single_data_chooser"]
        x_ordinate = values["single_x_ordinate"]
        y1_ordinate = values["single_y1_ordinate"]
        y2_ordinate = values["single_y2_ordinate"]
        y3_ordinate = values["single_y3_ordinate"]
        y4_ordinate = values["single_y4_ordinate"]
        try:
            single_update_plot(plot_block_id, x_ordinate, [y1_ordinate, y2_ordinate, y3_ordinate, y4_ordinate], window)
        except (IndexError, ValueError) as e:
            pass  # sg.popup(traceback.format_exc(), title="ERROR!", keep_on_top=True)
