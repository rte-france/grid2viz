import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd

from src.grid2kpi.episode import observation_model
from src.grid2kpi.manager import episode, agents, agent_ref

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}


def indicator_line(study_agent=agent_ref):
    return html.Div(className="lineBlock card", children=[
        html.H4("Indicators"),
        html.Div(className="card-body row", children=[

            html.Div(className="col-xl-2", children=[
                dcc.Dropdown(
                    id='agent_log_selector',
                    options=[{'label': agent, 'value': agent}
                             for agent in agents],
                    value=study_agent,
                    placeholder="Agent log"
                ),
                dcc.Loading(
                    [
                        html.Div(className="m-2", children=[
                            html.P(id="indicator_score_output",
                                   className="border-bottom h3 mb-0 text-right", children="NaN"),
                            html.P(className="text-muted", children="Score")
                        ]),
                        html.Div(className="m-2", children=[
                            html.P(id="indicator_nb_overflow",
                                   className="border-bottom h3 mb-0 text-right", children="NaN"),
                            html.P(className="text-muted",
                                   children="Number of Overflow")
                        ]),
                        html.Div(className="m-2", children=[
                            html.P(id="indicator_nb_action",
                                   className="border-bottom h3 mb-0 text-right", children="NaN"),
                            html.P(className="text-muted ",
                                   children="Number of Action")
                        ])
                    ]
                )
            ]),

            html.Div(className="col-xl-3", children=[
                html.H6(className="text-center",
                        children="Type Action Repartition"),
                dcc.Loading(
                    dcc.Graph(
                        id="agent_study_pie_chart",
                        figure=go.Figure(
                            layout=layout_def,
                        )
                    )
                )

            ]),

            html.Div(className="col-xl-7", children=[
                html.H6(className="text-center",
                        children="Action Maintenance Duration"),
                dcc.Loading(dcc.Graph(
                    id="maintenance_duration",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="bar")]
                    )
                ))
            ])
        ]),
    ])


overview_line = html.Div(id="overview_line_id", className="lineBlock card", children=[
    html.H4("Overview"),
    html.Div(className="card-body row", children=[

        html.Div(className="col-2", children=[
            dcc.Loading(
                dt.DataTable(
                    id="timeseries_table",
                    columns=[{"name": "Timestamps", "id": "Timestamps"}],
                    style_as_list_view=True,
                    row_deletable=True,
                    filter_action="native",
                    sort_action="native",
                    style_table={
                        'overflow-y': 'scroll',
                        'width': 'auto',
                        'height': '100%'
                    },
                )
            )

        ]),

        html.Div(className="col-10", children=[
            html.Div(className="row", children=[
                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Instant and Cumulated Reward"),
                    dcc.Graph(
                        id="cumulated_rewards_timeserie",
                        figure=go.Figure(
                            layout=layout_def,
                            # data=observation_model.get_df_rewards_trace(
                            #     episode)
                        )
                    )
                ]),

                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Overflow and Maintenances"),
                    dcc.Graph(
                        id="overflow_graph_study",
                        figure=go.Figure(
                            layout=layout_def,
                            data=[dict(type="scatter")]
                        )
                    )
                ]),
            ]),

            html.Div(className="row", children=[
                html.Div(className="col", children=[
                    html.H6(className="text-center", children="Actions"),
                    dcc.Graph(
                        id="action_timeserie",
                        figure=go.Figure(
                            layout=layout_def,
                            data=[dict(type="scatter")]
                        )
                    )
                ]),
                html.Div(className="col", children=[
                    html.H6(className="text-center",
                            children="Usage Rate"),
                    dcc.Graph(
                        id="usage_rate_graph_study",
                        figure=go.Figure(
                            layout=layout_def,
                            data=[dict(type="scatter")]
                        )
                    )
                ]),
            ]),
        ])
    ])
])

inspector_line = html.Div(className="lineBlock card ", children=[
    html.H4("Inspector"),
    html.Div(className="card-body col row", children=[
        html.Div(className="col", children=[
            dt.DataTable(
                id="inspector_datable",
                style_table={
                    'overflow': 'auto',
                    'width': '100%',
                    'max-width': '100%',
                    'height': '200px'
                },
            ),
            html.Label(children=[
                'The documentation for the filtering syntax can be found ',
                html.A('here.', href='https://dash.plot.ly/datatable/filtering', target="_blank")]),
        ]),

        html.Div(className="col-xl-12 row", children=[
            html.Div(className="col", children=[
                html.H6(className="text-center",
                        children="Distribution of Substation action"),
                dcc.Loading(
                    dcc.Graph(
                        id="distribution_substation_action_chart",
                        figure=go.Figure(
                            layout=layout_def,
                            data=[dict(type="bar")]
                        )
                    )
                )
            ]),
            html.Div(className="col", children=[
                html.H6(className="text-center",
                        children="Distribution of line action"),
                dcc.Loading(
                    dcc.Graph(
                        id="distribution_line_action_chart",
                        figure=go.Figure(
                            layout=layout_def,
                            data=[dict(type="bar")]
                        )
                    )
                )

            ]),
        ]),

    ])
])


def layout(study_agent=agent_ref):
    return html.Div(id="overview_page", children=[
        dcc.Store(id='relayoutStoreMacro'),
        indicator_line(study_agent),
        overview_line,
        inspector_line
    ])
