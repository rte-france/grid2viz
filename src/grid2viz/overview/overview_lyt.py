import dash_html_components as html
import dash_core_components as dcc
import dash_table as table
import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')  # TODO remove with backend working

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}
}

indicators_line = html.Div(children=[
    html.H2("Indicators"),
    html.Div(children=[

        html.Div(className="col-xl-5",
                 children=dcc.Graph(
                     id="indicator_line_charts",
                     figure=go.Figure(
                         layout=layout_def,
                         data=[
                             dict(type="scatter")
                         ]
                     )
                 )
                 ),

        html.Div(children=[dcc.Graph(
            figure=go.Figure(
                layout=layout_def,
                data=[go.Pie(
                    labels=['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen'],
                    values=[4500, 2500, 1053, 500]
                )]
            ))], className="col-xl-3"),

        html.Div(children=[
            html.Div(id="nb_steps", className="card text-center mb-4 p-2 w-75",
                     children=[html.H5(className="card-title", children="Steps"),
                               html.P(className="card-text", children="42")]),

            html.Div(id="nb_maintenance", className="card text-center p-2 w-75",
                     children=[html.H5(className="card-title", children="Maintenance"),
                               html.P(className="card-text", children="1")]),
        ], className="col-xl-2"),

        html.Div(children=[
            html.Div(id="nb_hazard", className="card text-center mb-4 p-2 w-75",
                     children=[html.H5(className="card-title", children="Hazard"),
                               html.P(className="card-text", children="3")]),

            html.Div(id="maintenance_duration", className="card text-center p-2 w-75",
                     children=[html.H5(className="card-title", children="Duration Maintenance"),
                               html.P(className="card-text", children="3")])

        ], className="col-xl-2")
    ], className="card-body row "),
], className="lineBlock card")

summary_line = html.Div(children=[
    html.H2("Summary"),
    html.Div(children=[
        html.Div(children=[
            html.H2("Environments Time Series"),
            dcc.Dropdown(
                id='input_env_selector',
                options=[{'label': 'Load', "value": "1"}, {'label': 'Production', "value": "2"}],
            ),
            dcc.Graph(id='input_env_charts',
                      figure=go.Figure(
                          layout=layout_def,
                          data=[
                              dict(type="scatter")
                          ]))
        ], className="col-xl-5"),
        html.Div(children=[
            dcc.Graph(id='usage_rate_and_overview',
                      style={'margin-top': '2.5em'},
                      figure=go.Figure(
                          layout=layout_def,
                          data=[
                              dict(type="scatter")
                          ]))
        ], className="col-xl-5"),
        html.Div(children=[
            html.Img(src="https://www.autourdelacom.fr/wp-content/uploads/2018/03/default-user-image.png",
                     className="w-25 mb-2 mx-auto"),  # TODO add font awesome
            dcc.Dropdown(
                id="input_agent_selector", placeholder="select a ref agent",
                options=[{'label': 'test', 'value': 1},
                         {'label': 'test1', 'value': 2}]
            ),
        ], className="col-xl-2 align-self-center"),
    ], className="card-body row"),
], className="lineBlock card")

ref_agent_line = html.Div(children=[
    html.H2("Inspector"),
    html.Div(children=[
        table.DataTable(
            id="inspection_table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
        )
    ], className="p-5")

], className="lineBlock card")

layout = html.Div(id="overview_line", children=[
    indicators_line,
    summary_line,
    ref_agent_line
])
