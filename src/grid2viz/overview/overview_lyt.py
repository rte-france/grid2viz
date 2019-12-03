import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
import plotly.graph_objects as go
import pandas as pd
from src.grid2kpi.episode import observation_model


share_prod = observation_model.get_prod()

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
                    labels=share_prod["equipment"],
                    values=share_prod.groupby("equipment")["value"].sum()
                )]
            ))], className="col-xl-4"),

        # number summary column
        html.Div(children=[
            html.Div(children=[
                html.Div(id="nb_steps", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Steps"),
                                   html.P(className="card-text", children="42")]),

                html.Div(id="nb_maintenance", className="card text-center p-2",
                         children=[html.H5(className="card-title", children="Maintenance"),
                                   html.P(className="card-text", children="1")]),
            ], className="col-6"),
            html.Div(children=[
                html.Div(id="nb_hazard", className="card text-center p-2 mb-4",
                         children=[html.H5(className="card-title", children="Hazard"),
                                   html.P(className="card-text", children="3")]),

                html.Div(id="maintenance_duration", className="card text-center p-2",
                         children=[html.H5(className="card-title", children="Duration Maintenance"),
                                   html.P(className="card-text", children="3")])
            ], className="col-6")
        ], className="col-xl-3 row align-self-center")
    ], className="card-body row"),
], className="lineBlock card")

summary_line = html.Div(children=[
    html.H2("Summary"),
    html.Div(children=[
        html.Div(children=[
            html.H3("Environments Time Series"),
            dcc.Dropdown(
                id='input_env_selector',
                options=[{'label': 'Load', "value": "1"}, {
                    'label': 'Production', "value": "2"}],
            ),
            dcc.Graph(id='input_env_charts',
                      figure=go.Figure(
                          layout=layout_def,
                          data=[
                              dict(type="scatter")
                          ]))
        ], className="col-xl-5"),

        html.Div(children=[
            html.H3("Usage rate and overview"),
            dcc.Dropdown(
                id="input_agent_selector", placeholder="select a ref agent",
                options=[{'label': 'test', 'value': 1},
                         {'label': 'test1', 'value': 2}]
            ),
            html.Div(children=[
                dcc.Graph(
                    id='usage_rate_graph',
                    className="col-6",
                    style={'margin-top': '2.5em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=[
                            dict(type="scatter")
                        ])
                ),
                dcc.Graph(
                    id='usage_overview_graph',
                    className="col-6",
                    style={'margin-top': '2.5em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=[
                            dict(type="scatter")
                        ])
                ),
            ], className="row"),
        ], className="col-xl-6"),
    ], className="card-body row"),
], className="lineBlock card")

ref_agent_line = html.Div(children=[
    html.H2("Inspector"),
    html.Div(children=[
        dt.DataTable(
            id="inspection_table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=10,
        )
    ], className="p-2")
], className="lineBlock card")

layout = html.Div(id="overview_page", children=[
    indicators_line,
    summary_line,
    ref_agent_line
])
