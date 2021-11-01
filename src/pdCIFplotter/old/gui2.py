import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import dash_uploader as du
import tempfile
import uuid

data_list = \
    [
        {'label': 'Stacked', 'value': 'stacked'},
        {'label': 'Surface', 'value': 'surface'},
        {'label': 'pattern_0', 'value': 'pattern_0'},
        {'label': 'pattern_1', 'value': 'pattern_1'},
        {'label': 'pattern_2', 'value': 'pattern_2'},
        {'label': 'pattern_3', 'value': 'pattern_3'},
        {'label': 'pattern_4', 'value': 'pattern_4'},
        {'label': 'pattern_5', 'value': 'pattern_5'},
        {'label': 'pattern_6', 'value': 'pattern_6'},
        {'label': 'pattern_7', 'value': 'pattern_7'},
        {'label': 'pattern_8', 'value': 'pattern_8'},
        {'label': 'pattern_9', 'value': 'pattern_9'},
        {'label': 'pattern_10', 'value': 'pattern_10'}
    ]

tmp_dir = tempfile.TemporaryDirectory()
print(tmp_dir.name)


app = dash.Dash(__name__)

du.configure_upload(app, tmp_dir.name)

def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1800,  # 1800 Mb
        filetypes=['cif', 'state'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


def get_app_layout():

    return html.Div(
        [
            html.H1('Demo'),
            html.Div(
                [
                    get_upload_component(id='dash-uploader'),
                    html.Div(id='callback-output'),
                    html.Div(dcc.Dropdown('data-chooser-dropdown', data_list, data_list[2]["value"]), id="dropdown-div")
                ],
                style={  # wrapper div style
                    'textAlign': 'center',
                    'width': '600px',
                    'padding': '10px',
                    'display': 'inline-block'
                }),
        ],
        style={
            'textAlign': 'center',
        },
    )


# get_app_layout is a function
# This way we can use unique session id's as upload_id's
app.layout = get_app_layout


# this callback decorator is designed to be automatically called after the upload completes.
# This example gives a list of the filenames uploaded, with their absolute paths.
@du.callback(
    output=Output('callback-output', 'children'),
    id='dash-uploader',
)
def get_a_list(filenames):
    return html.Ul([html.Li(filenames)])


if __name__ == '__main__':
    app.run_server(debug=False)