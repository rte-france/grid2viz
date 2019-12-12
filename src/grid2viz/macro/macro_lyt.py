import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd

from src.grid2kpi.episode import observation_model
from src.grid2kpi.manager import episode, agents

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

df = pd.read_csv(
    'https://raw.githubusercontent.com/plotly/datasets/master/solar.csv')  # TODO remove with backend working

indicator_line = html.Div(className="lineBlock card", children=[
    html.H4("Indicators"),
    html.Div(className="card-body row", children=[

        html.Div(className="col-xl-2", children=[
            dcc.Dropdown(
                id='agent_log_selector',
                options=[{'label': agent, 'value': agent} for agent in agents],
                placeholder="Agent log"
            ),

            html.Div(className="m-2", children=[
                html.P(id="indicator_score_output", className="border-bottom h3 mb-0 text-right", children="NaN"),
                html.P(className="text-muted", children="Score")
            ]),
            html.Div(className="m-2", children=[
                html.P(id="indicator_nb_overflow", className="border-bottom h3 mb-0 text-right", children="NaN"),
                html.P(className="text-muted", children="Number of Overflow")
            ]),
            html.Div(className="m-2", children=[
                html.P(id="indicator_nb_action", className="border-bottom h3 mb-0 text-right", children="NaN"),
                html.P(className="text-muted ", children="Number of Action")
            ])
        ]),

        html.Div(className="col-xl-3", children=[
            html.H6(className="text-center", children="Type Action Repartition"),
            dcc.Graph(
                figure=go.Figure(
                    layout=layout_def,
                    data=[go.Pie(
                        labels=['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen'],
                        values=[4500, 2500, 1053, 500]
                    )],
                )
            )
        ]),

        html.Div(className="col-xl-7", children=[
            html.H6(className="text-center", children="Action Maintenance Duration"),
            dcc.Graph(
                figure=go.Figure(
                    layout=layout_def,
                    data=[dict(type="bar")]
                )
            )
        ])
    ]),
])

overview_line = html.Div(id="overview_line_id", className="lineBlock card container", children=[
    html.H4("Overview"),
    html.Div(className="card-body row", children=[

        html.Div(className="col row", children=[
            dt.DataTable(
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
            )
        ]),

        html.Div(className="col row", children=[
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Instant and Cumulated Reward"),
                dcc.Graph(
                    id="cumulated_rewards_timeserie",
                    figure=go.Figure(
                        layout=layout_def,
                        data=observation_model.get_df_rewards_trace(episode)
                    )
                )
            ]),
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Actions"),
                dcc.Graph(
                    id="action_timeserie",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    ),
                )
            ]),
        ]),

        html.Div(className="col row", children=[
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Usage Rate"),
                dcc.Graph(
                    id="usage_rate_graph_study",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    )
                )
            ]),
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Usage Overflow"),
                dcc.Graph(
                    id="overflow_graph_study",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    )
                )
            ]),
        ]),
    ])
])

inspector_line = html.Div(className="lineBlock card ", children=[
    html.H4("Inspector"),
    html.Div(className="card-body col row", children=[

        html.Div(className="col row", children=[
            dt.DataTable(
                id="inspector_datable",
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict('records'),
                style_table={
                    'overflow': 'auto',
                    'width': '100%',
                    'max-width': '100%',
                    'height': '200px'
                },
            )]),
        html.Div(className="col-xl-12 row", children=[
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Distribution of Substation action"),
                dcc.Graph(
                    id="distribution_substation_action_chart",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="bar")]
                    )
                )
            ]),
            html.Div(className="col", children=[
                html.H6(className="text-center", children="Distribution of line action"),
                dcc.Graph(
                    id="distribution_line_action_chart",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="bar")]
                    )
                )
            ]),
        ]),

    ])
])

layout = html.Div(id="overview_page", children=[
    indicator_line,
    overview_line,
    inspector_line
])
