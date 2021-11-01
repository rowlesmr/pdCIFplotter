import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd

df = pd.read_csv("../../data/short.txt")

#to get all the posisble types from the loaded data
types = [{"label": str(t), "value": t} for t in df["type"].unique()]


#get the y values that are in the loaded data
possible_ys = {"y1", "y2", "y3", "y4"}  # this is a set
df_cols = set(df.columns)
df_ys_list = list(possible_ys.intersection(df_cols))

df_ys = [{"label": str(t), "value": str(t)} for t in df_ys_list]



app = dash.Dash()

app.layout = html.Div(children=[
    dcc.Graph(id="plot"),
    dcc.Dropdown(id="type_chooser", options=types, value=df["type"][0]),
    dcc.Dropdown(id="y_chooser", options=df_ys, clearable=True)
])


@app.callback(Output("plot", component_property="figure"),
              [Input("type_chooser", component_property="value"),
               Input("y_chooser", component_property="value")])
def update_plot(new_type, new_y):
    filtered_df = df[df["type"] == new_type]
    traces = [go.Scatter(x=filtered_df["x"], y=filtered_df[new_y], mode="markers", name=new_y)]
    return {"data": traces, "layout": go.Layout()}


if __name__ == '__main__':
    app.run_server()
