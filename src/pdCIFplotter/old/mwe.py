import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])

app.layout = \
    dbc.Container \
            ([
            dbc.Row([
                dbc.Col
                    ([
                    dbc.Row([dbc.Button("Graph here", style={"width": "100%"})]), # make this fill the available height
                    dbc.Row([dbc.Button("Load file",  style={"width": "50%"}), dbc.Button("Load a different file") # make this button fill available width]),
                ], width=9),
                dbc.Col
                    ([
                    dbc.Row([dbc.Button("Choose data",  style={"width": "100%"})]),
                    dbc.Row([dbc.Button("Change graph", style={"width": "100%"})]), # make this fill available height
                ], width=3)
            ])
        ], fluid=True)

if __name__ == "__main__":
    app.run_server(debug=False, port=8050)
