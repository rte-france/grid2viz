import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')  # TODO remove with backend working

indicator_line = html.Div(className="lineBlock card", children=[
    html.H2("Indicators"),
    html.Div(className="card-body row", children=[
        html.Div(className="col-xl-2", children=[dcc.Dropdown(
            id='agent_log_selector',
            options=[{'label': 'test', "value": "1"}, {'label': 'test2', "value": "2"}],
            placeholder="Load agent log for study"
        ),
            html.Div(className="", children=[
                html.Div(className="card m-2", children=[
                    html.H5("Score"),
                    html.P(1)
                ]),
                html.Div(className="card m-2", children=[
                    html.H5("Overflows"),
                    html.P(5000)
                ]),
                html.Div(className="card m-2", children=[
                    html.H5("Actions"),
                    html.P(100)
                ])
            ])
        ]),

        html.Div(className="col-xl-4", children=[dcc.Graph(
            figure=go.Figure(
                layout=layout_def,
                data=[go.Pie(
                    labels=['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen'],
                    values=[4500, 2500, 1053, 500]
                )],
            )
        )]),

        html.Div(className="col-xl-6", children=[dcc.Graph(
            figure=go.Figure(
                layout=layout_def,
                data=[dict(type="bar")]
            )
        )])
    ]),
])

overview_line = html.Div(className="lineBlock card", children=[
    html.H2("Overview"),
    html.Div(className="card-body row", children=[

        html.Div(className="col-xl-2", children=[dt.DataTable(
            id="timeseries_table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'),
            style_as_list_view=True,
            row_deletable=True,
            style_table={
                'overflow': 'auto',
                'width': 'auto',
                'height': '100%'
            },
        )]),

        html.Div(className="col-xl-6 row", children=[
            html.Div(className="col-12", children=[
                dcc.Graph(
                    id="cumulated_rewards_timeserie",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    )),
                html.H6(className="text-center", children="Instant and Cumulated Reward")
            ]),
            html.Div(className="col-xl-12", children=[
                dcc.Graph(
                    id="action_timeserie",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    ),
                ),
                html.H6(className="text-center", children="Actions")
            ]),
        ]),

        html.Div(className="col-xl-4 row", children=[
            html.Div(className="col-12", children=[dcc.Graph(
                id="usage_rate",
                figure=go.Figure(
                    layout=layout_def,
                    data=[dict(type="scatter")]
                )
            )]),
            html.Div(className="col-12", children=[dcc.Graph(
                id="usage_overflow",
                figure=go.Figure(
                    layout=layout_def,
                    data=[dict(type="scatter")]
                )
            )]),
        ]),
    ])
])

layout = html.Div(id="overview_page", children=[
    indicator_line,
    overview_line,
    # inspector_line
])
