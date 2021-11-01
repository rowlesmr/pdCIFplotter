import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash_daq as daq
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# This will eventually be set through the user uploading a copy of their CIF.
# For now, I just want to get it running.
df = pd.read_table("../../data/diff_data.txt")
# this bit would normally be done in the cif reading ot
df["d"] = df["_diffrn_radiation_wavelength"] / (2 * np.sin(df["_pd_meas_2theta_scan"] * np.pi / 360.))
df["q"] = 2 * np.pi / df["d"]

# todo: this will have to be a dictionary that allows lookup by data name, in case it changes per pattern
wavelength = 0.8257653  # just for argument's sake
if wavelength is not None:
    _lam = f"(\u03BB = {str(wavelength)} \u212b)"
else:
    _lam = ""

##


data_list = [{'label': 'Stacked', 'value': 'stacked'}, {'label': 'Surface', 'value': 'surface'}] + \
            [{"label": str(val), "value": str(val)} for val in df["_pd_block_id"].unique()]

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

marker_style_dict_list = [
    {"label": "circle", "value": "circle"},
    {"label": "square", "value": "square"},
    {"label": "diamond", "value": "diamond"},
    {"label": "cross", "value": "cross"},
    {"label": "x", "value": "x"},
    {"label": "triangle-up", "value": "triangle-up"},
    {"label": "triangle-down", "value": "triangle-down"},
    {"label": "triangle-left", "value": "triangle-left"},
    {"label": "triangle-right", "value": "triangle-right"},
    {"label": "triangle-ne", "value": "triangle-ne"},
    {"label": "triangle-se", "value": "triangle-se"},
    {"label": "triangle-sw", "value": "triangle-sw"},
    {"label": "triangle-nw", "value": "triangle-nw"},
    {"label": "pentagon", "value": "pentagon"},
    {"label": "hexagon", "value": "hexagon"},
    {"label": "hexagon2", "value": "hexagon2"},
    {"label": "octagon", "value": "octagon"},
    {"label": "star", "value": "star"},
    {"label": "hexagram", "value": "hexagram"},
    {"label": "star-triangle-up", "value": "star-triangle-up"},
    {"label": "star-triangle-down", "value": "star-triangle-down"},
    {"label": "star-square", "value": "star-square"},
    {"label": "star-diamond", "value": "star-diamond"},
    {"label": "diamond-tall", "value": "diamond-tall"},
    {"label": "diamond-wide", "value": "diamond-wide"},
    {"label": "hourglass", "value": "hourglass"},
    {"label": "bowtie", "value": "bowtie"},
    {"label": "circle-cross", "value": "circle-cross"},
    {"label": "circle-x", "value": "circle-x"},
    {"label": "square-cross", "value": "square-cross"},
    {"label": "square-x", "value": "square-x"},
    {"label": "diamond-cross", "value": "diamond-cross"},
    {"label": "diamond-x", "value": "diamond-x"},
    {"label": "cross-thin", "value": "cross-thin"},
    {"label": "x-thin", "value": "x-thin"},
    {"label": "asterisk", "value": "asterisk"},
    {"label": "hash", "value": "hash"},
    {"label": "y-up", "value": "y-up"},
    {"label": "y-down", "value": "y-down"},
    {"label": "y-left", "value": "y-left"},
    {"label": "y-right", "value": "y-right"},
    {"label": "line-ew", "value": "line-ew"},
    {"label": "line-ns", "value": "line-ns"},
    {"label": "line-ne", "value": "line-ne"},
    {"label": "line-nw", "value": "line-nw"},
    {"label": "arrow-up", "value": "arrow-up"},
    {"label": "arrow-down", "value": "arrow-down"},
    {"label": "arrow-left", "value": "arrow-left"},
    {"label": "arrow-right", "value": "arrow-right"},
    {"label": "arrow-bar-up", "value": "arrow-bar-up"},
    {"label": "arrow-bar-down", "value": "arrow-bar-down"},
    {"label": "arrow-bar-left", "value": "arrow-bar-left"},
    {"label": "arrow-bar-right", "value": "arrow-bar-right"}]


def make_dictionary_for_dropdown(complete_list, possible_list):
    used_list = []
    for t in complete_list:
        if t in possible_list:
            used_list.append(t)
    return [{"label": complete_xy_plaintext_dict[t], "value": t} for t in used_list]


x_list = make_dictionary_for_dropdown(complete_x_list, list(df.columns))
y_list = make_dictionary_for_dropdown(complete_y_list, list(df.columns))

scale_list = \
    [
        {'label': 'Linear  ', 'value': 'linear'},
        {'label': 'Sqrt  ', 'value': 'sqrt'},
        {'label': 'Log', 'value': 'log'}
    ]
right_div_label_width = "20%"
right_div_wide_dropdown_width = "80%"
right_div_narrow_dropdown_width = "55%"
right_div_button_width = "25%"


def data_chooser(label, idn, options, value):
    return html.Div([
        html.Div(label,
                 style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_label_width}),
        html.Div(dcc.Dropdown(id=idn, options=options, value=value),
                 style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_wide_dropdown_width}),
    ])


def x_ordinate_chooser(label, idn, options, value):
    return data_chooser(label, idn, options, value)


def y_ordinate_modal(idn, header, colour_default, lm_default, marker_default, line_default, size_default):
    return dbc.Modal(
        [
            dbc.ModalHeader(header),
            dbc.ModalBody(
                [
                    html.Div([  # left div
                        daq.ColorPicker(
                            id={"type": "modal-colour-picker", "id": idn},
                            label='Color Picker',
                            value=colour_default  # {"hex": '#119DFF'}
                        )
                    ], style={"width": "50%", 'display': 'inline-block', "align": "top"}),
                    # complete_xy_plaintext_dict[t]
                    html.Div([  # right div
                        html.Div(["Lines/markers"]),
                        html.Div([
                            dcc.Dropdown(
                                id={"type": "modal-linesmarkers-dropdown", "id": idn},
                                options=[
                                    {"label": "Lines", "value": 'lines'},
                                    {"label": "Markers", "value": "markers"},
                                    {"label": "Lines & markers", "value": "lines+markers"}
                                ],
                                value=lm_default
                            )
                        ]),
                        html.Div(["Marker style"]),
                        html.Div([
                            dcc.Dropdown(
                                id={"type": "modal-markerstyle-dropdown", "id": idn},
                                options=marker_style_dict_list,
                                value=marker_default
                            )

                        ]),
                        html.Div(["Line style"]),  # ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']
                        html.Div([
                            dcc.Dropdown(
                                id={"type": "modal-linestyle-dropdown", "id": idn},
                                options=[
                                    {"label": "Solid", "value": 'solid'},
                                    {"label": "Dot", "value": "dot"},
                                    {"label": "Dash", "value": "dash"},
                                    {"label": "Long dash", "value": "longdash"},
                                    {"label": "Dash dot", "value": "dashdot"},
                                    {"label": "Long dash dot", "value": "longdashdot"},
                                ],
                                value=line_default
                            )
                        ]),
                        html.Div(["Size"]),  # does both line and marker
                        html.Div([
                            dcc.Dropdown(
                                id={"type": "modal-size-dropdown", "id": idn},
                                options=[{"label": str(size), "value": size} for size in range(1, 30)],
                                value=size_default
                            )
                        ]),
                    ], style={"width": "48%", 'display': 'inline-block', "align": "top", "padding-left": "2%"})
                ]
            ),
            dbc.ModalFooter(
                dbc.Button("Close", id={"type": "close-modal", "id": idn}, className="ml-auto", n_clicks=0)),
        ],
        id={"type": "modal", "id": idn},
        is_open=False
    )


def y_ordinate_chooser(label, idn, options, value, colour_default, lm_default, marker_default, line_default,
                       size_default):
    return html.Div([
        html.Div(label,
                 style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_label_width}),
        html.Div(dcc.Dropdown(id=idn, options=options, value=value),
                 style={'display': 'inline-block', 'vertical-align': 'middle',
                        "width": right_div_narrow_dropdown_width}),
        html.Div([dbc.Button("Options", id={"type": "options", "id": idn}, color="primary", className="mr-1",
                             active=True, n_clicks=0),
                  y_ordinate_modal(idn, label, colour_default, lm_default, marker_default, line_default, size_default)],
                 style={'display': 'inline-block', 'vertical-align': 'middle',
                        "width": right_div_button_width, "padding-left": "5px"}),
    ], style={"padding-top": "5px"})


def offset_chooser(label, idn, value):
    return html.Div([
        html.Div(label,
                 style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_label_width}),
        html.Div(dcc.Input(
            id=idn,
            placeholder='Enter a value...',
            type='number',
            value=value
        ),
            style={'display': 'inline-block', 'vertical-align': 'middle',
                   "width": right_div_narrow_dropdown_width}),
    ], style={"padding-top": "5px"})


def axis_scale_chooser(label, idn, options, value):
    return html.Div([
        html.Div(label, style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_label_width}),
        html.Div(
            dcc.RadioItems(id=idn, options=options, value=value,
                           labelStyle={'display': 'inline-block', "margin-left": "10px"},
                           inputStyle={"margin-right": "5px"}),
            style={'display': 'inline-block', 'vertical-align': 'middle', "width": right_div_wide_dropdown_width})
    ])


def checkmark_choose(idn):
    return html.Div([
        html.Div(dcc.Checklist(
            id=idn,
            options=[
                {'label': 'Show HKL ticks', 'value': 'hkl'},
                {'label': 'Fill under traces', 'value': 'tozeroy'},
                {'label': 'Normalise intensity', 'value': 'norm'},
                # {'label': 'Show labels', 'value': 'labels'}
            ],
            value=["tozeroy"],
            inputStyle={"margin-right": "5px"}),
            style={'display': 'inline-block',
                   'vertical-align': 'top',
                   "width": "55%"}),
        html.Div(dcc.RadioItems(id=idn + "-radio",
                                options=[
                                    {"label": "Above", "value": "above"},
                                    {"label": "Below", "value": "below"}
                                ],
                                value="below",
                                labelStyle={'display': 'inline-block', "margin-left": "10px"},
                                inputStyle={"margin-right": "5px"}),
                 style={'display': 'inline-block',
                        'vertical-align': 'top'}),
    ])


def load_files(idn):
    return html.Div([
        dcc.Upload(
            id=idn,
            children=html.Div(['Drag and drop CIF or State file, or ', html.A('click to select file')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center'
            },
            # Allow multiple files to be uploaded
            multiple=False
        ),
        dbc.Button("Download State", color="primary", className="mr-1", active=True)
    ], style={"width": "100%", 'display': 'inline-block'}
    )


app = dash.Dash(__name__, title="pdCIFplotter", external_stylesheets=[dbc.themes.CERULEAN])

app.layout = html.Div(children=  # main div
[
    html.Div(children=  # left div
    [
        html.Div(children=  # plot goes here!
        [
            dcc.Graph("plot", style={'width': '100%', 'height': '100%'}, config={"displaylogo": False})
        ],
            style={'height': "84vh"}),  # "border": "2px green solid"
        html.Div(children=  # file open, state saver
        [
            load_files("file-upload")
        ],
            style={'height': "15vh"})
    ],
        # left div
        style={'width': "75%",
               'display': 'inline-block',
               'vertical-align': 'top'}
    ),
    html.Div(children=  # right div
    [
        html.Div(children=  # plot chooser
        [
            data_chooser("Data", 'data-chooser-dropdown', data_list, data_list[0]["value"]),
        ],
            style={'height': "10vh", 'vertical-align': 'middle'}),
        html.Div(children=  # plot controls
        [
            # ---
            x_ordinate_chooser("X axis", "x-chooser-dropdown", x_list, x_list[0]["value"]),
            y_ordinate_chooser("Y axis", "y-chooser-dropdown", y_list, y_list[0]["value"], dict(hex='#000000'),
                               "lines", "circle", "solid", 6),
            offset_chooser("Offset", "offset-value", 100),
            # ---
            # ---
            html.P(),
            # ---
            checkmark_choose("checkmark"),
            # ---
            html.P(),
            # ---
            axis_scale_chooser("X scale", "x-scale-radio", scale_list, scale_list[0]["value"]),
            axis_scale_chooser("Y scale", "y-scale-radio", scale_list, scale_list[0]["value"]),
            # ---
        ],
            style={'height': "89vh"})
    ],
        # right div
        style={'width': "25%",
               'display': 'inline-block',
               'vertical-align': 'top'}
    ),
],
    # main div
    style={'width': "100%", 'height': "100vh"}
)

slow = 1
if slow:
    @app.callback(Output("plot", component_property="figure"),
                  [Input("data-chooser-dropdown", component_property="value"),
                   Input("x-chooser-dropdown", component_property="value"),
                   Input("y-chooser-dropdown", component_property="value"),
                   Input("offset-value", component_property="value"),
                   Input({"type": "modal-colour-picker", "id": "y-chooser-dropdown"}, component_property="value"),
                   Input({"type": "modal-linesmarkers-dropdown", "id": "y-chooser-dropdown"},
                         component_property="value"),
                   Input({"type": "modal-markerstyle-dropdown", "id": "y-chooser-dropdown"},
                         component_property="value"),
                   Input({"type": "modal-linestyle-dropdown", "id": "y-chooser-dropdown"},
                         component_property="value"),
                   Input({"type": "modal-size-dropdown", "id": "y-chooser-dropdown"}, component_property="value"),
                   Input("x-scale-radio", component_property="value"),
                   Input("y-scale-radio", component_property="value")
                   ])
    def update_plot_traces(data, x_ordinate, y_ordinate, offset,
                           y_colour, y_linesmarkers, y_markerstyle, y_linestyle, y_size,
                           x_scale, y_scale):
        if "intensity" in y_ordinate:
            y_axis_title = "Intensity (arb. units; patterns are vertically offet)"
        else:
            y_axis_title = "Counts (patterns are vertically offset)"

        traces = []

        x = df[x_ordinate].to_numpy()
        # x = df["d"].to_numpy()
        y = pd.factorize(df._pd_block_id)[0]
        z = df[y_ordinate].to_numpy()

        traces.append(go.Heatmap(x=x, y=y, z=z, colorscale='Viridis'))


        #
        # things = df["_pd_block_id"].unique()
        # for i in range(len(things) - 1, -1, -1):  # go through the loop backwards so the plots are in the correct order
        #     filtered_df = df[df["_pd_block_id"] == things[i]]
        #     traces.append(go.Scatter(x=filtered_df[x_ordinate],
        #                              y=filtered_df[y_ordinate] + i * offset,
        #                              name=y_ordinate,
        #                              meta="y" + str(i),
        #                              hovertext=things[i],
        #                              mode=y_linesmarkers,
        #                              line={"dash": y_linestyle, "color": y_colour["hex"], "width": y_size / 3},
        #                              marker={"symbol": y_markerstyle, "color": y_colour["hex"], "size": y_size},
        #                              fill="tozeroy",
        #                              fillcolor="white"
        #                              )
        #                   )

        layout = go.Layout(title={"text": data, "x": 0.1},
                           xaxis={"title": x_axis_titles[x_ordinate], "showline": True, "linewidth": 1,
                                  "linecolor": 'grey', "mirror": True, "ticks": "inside", "type": x_scale},
                           yaxis={"title": y_axis_title, "showline": True, "linewidth": 1, "linecolor": 'gray',
                                  "mirror": True, "ticks": "inside", "type": y_scale},
                           legend={"orientation": "v", "yanchor": "top", "y": 0.99, "xanchor": "right", "x": 1,
                                   "bgcolor": 'rgba(0,0,0,0)'},
                           margin={"t": 50, "r": 40, "b": 80, "l": 80},
                           uirevision="never",
                           showlegend=False)

        return {"data": traces, "layout": layout}

else:
    @app.callback(Output("plot", component_property="figure"),
                  [Input("data-chooser-dropdown", component_property="value"),
                   Input("x-chooser-dropdown", component_property="value"),
                   Input("y-chooser-dropdown", component_property="value"),
                   Input("offset-value", component_property="value"),
                   Input("x-scale-radio", component_property="value"),
                   Input("y-scale-radio", component_property="value")
                   ])
    def update_plot_traces(data, x_ordinate, y_ordinate, offset, x_scale, y_scale):
        if "intensity" in y_ordinate:
            y_axis_title = "Intensity (arb. units; patterns are vertically offet)"
        else:
            y_axis_title = "Counts (patterns are vertically offset)"

        traces = []
        things = df["_pd_block_id"].unique()
        # go through the list backwards so the traces are put in the correct order
        for i in range(len(things) - 1, -1, -1):
            filtered_df = df[df["_pd_block_id"] == things[i]]

            traces.append(go.Scatter(x=filtered_df[x_ordinate],
                                     y=filtered_df[y_ordinate] + i * offset,
                                     name=y_ordinate,
                                     meta="y" + str(i),
                                     hovertext=things[i],
                                     fill="tozeroy",
                                     fillcolor="white"
                                     )
                          )

        layout = go.Layout(title={"text": data, "x": 0.1},
                           xaxis={"title": x_axis_titles[x_ordinate], "showline": True, "linewidth": 1,
                                  "linecolor": 'grey', "mirror": True, "ticks": "inside", "type": x_scale},
                           yaxis={"title": y_axis_title, "showline": True, "linewidth": 1, "linecolor": 'gray',
                                  "mirror": True, "ticks": "inside", "type": y_scale},
                           legend={"orientation": "v", "yanchor": "top", "y": 0.99, "xanchor": "right", "x": 1,
                                   "bgcolor": 'rgba(0,0,0,0)'},
                           margin={"t": 50, "r": 40, "b": 80, "l": 80},
                           uirevision="never",
                           showlegend=False)

        return {"data": traces, "layout": layout}


@app.callback(
    Output({"type": "modal", "id": MATCH}, "is_open"),
    [Input({"type": "options", "id": MATCH}, "n_clicks"), Input({"type": "close-modal", "id": MATCH}, "n_clicks")],
    [State({"type": "modal", "id": MATCH}, "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
