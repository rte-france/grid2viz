import dash_html_components as html
import dash_core_components as dcc
import dash_antd_components as dac
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd
import numpy as np
import datetime

from src.grid2kpi.episode_analytics import observation_model
from src.grid2kpi.manager import (
    episode, make_episode, base_dir, indx, make_network, get_network_graph)

layout_def = {
    'legend': {'orientation': 'h'},
    "showlegend": True,
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

indicator_line = html.Div(id="indicator_line_id", className="lineBlock card", children=[
    html.H4("Indicators"),
    html.Div(className="card-body row", children=[
        html.Div(className="col-xl-6", children=[
            html.H6(className="text-center",
                    children="Rewards instant + cumulated for 2 agent"),
            dcc.Graph(
                id="cum_instant_reward_ts",
                figure=go.Figure(
                    layout=layout_def,
                    data=[dict(type="bar")]
                )
            )
        ]),

        html.Div(className="col-xl-6", children=[
            html.H6(className="text-center",
                    children="Actions"),
            dcc.Graph(
                id="actions_ts",
                figure=go.Figure(
                    layout=layout_def,
                    data=[dict(type="bar")]
                )
            )
        ])
    ])
])


def flux_inspector_line(network_graph=None):

    return html.Div(id="flux_inspector_line_id", className="lineBlock card", children=[
        html.H4("Flow"),
        html.Div(className="card-body row", children=[
            html.Div(className="col", children=[
                html.Div(className="row", children=[

                    html.Div(className="col", children=[
                        html.H6(className="text-center",
                                children="Interactive Graph"),

                        dcc.Graph(
                            id="interactive_graph",
                            figure=network_graph
                        )
                    ])
                ]),
                html.Div(className="row", children=[
                    html.Div(className="col", children=[
                        html.H6(className="text-center",
                                children="Voltage and Flow"),
                        dac.Radio(options=[
                            {'label': 'Flow', "value": "flow"},
                            {'label': 'Voltage', "value": "voltage"},
                        ],
                            value="flow",
                            id="voltage_flow_selector",
                            buttonStyle="solid"
                        ),
                        dac.Select(
                            id="line_side_choices",
                            options=[],
                            value=[],
                            mode='multiple',
                            showArrow=True
                        ),
                        dcc.Graph(
                            id="voltage_flow_graph",
                            figure=go.Figure(
                                layout=layout_def,
                                data=[dict(type="scatter")]
                            )
                        )
                    ]),
                ])
            ])
        ])
    ])


context_inspector_line = html.Div(id="context_inspector_line_id", className="lineBlock card ", children=[
    html.H4("Context"),
    html.Div(className="card-body col row", children=[

        html.Div(className="col-xl-5", children=[
            html.H5("Environments Time Series"),
            dac.Radio(options=[
                {'label': 'Load', "value": "Load"},
                {'label': 'Production', "value": "Production"},
                {'label': 'Hazards', "value": "Hazards"},
                {'label': 'Maintenances', "value": "Maintenances"},
            ],
                value="Load",
                id="environment_choices_buttons",
                buttonStyle="solid"
            ),
            dac.Select(
                id='asset_selector',
                options=[{'label': load_name,
                          'value': load_name}
                         for load_name in episode.load_names],
                value=episode.load_names[0],
                mode='multiple',
                showArrow=True
            ),
            dcc.Graph(
                id='env_charts_ts',
                style={'margin-top': '1em'},
                figure=go.Figure(layout=layout_def),
                config=dict(displayModeBar=False)
            ),
        ]),

        html.Div(className="col-xl-7", children=[
            html.H5("OverFlow and Usage rate"),
            html.Div(className="row", children=[
                dcc.Graph(
                    id='usage_rate_ts',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=observation_model.get_usage_rate_trace(episode)
                    ),
                    config=dict(displayModeBar=False)
                ),
                dcc.Graph(
                    id='overflow_ts',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=observation_model.get_total_overflow_trace(
                            episode)
                    ),
                    config=dict(displayModeBar=False)
                ),
            ], ),
        ]),

    ])
])

all_info_line = html.Div(id="all_info_line_id", className="lineBlock card ", children=[
    html.H4("All"),
    html.Div(className="card-body col row", children=[

        html.Div(className="col-xl-10", children=[
            dt.DataTable(
                id="all_info_table",
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_action="native",
                page_current=0,
                page_size=20,
            )
        ])
    ])
])


def compute_window(user_selected_timestamp, study_agent):
    if user_selected_timestamp is not None:
        n_clicks_left = 0
        n_clicks_right = 0
        new_episode = make_episode(base_dir, study_agent, indx)
        center_indx = new_episode.timestamps.index(
            datetime.datetime.strptime(
                user_selected_timestamp, '%Y-%m-%d %H:%M')
        )
        timestamp_range = new_episode.timestamps[
            max([0, (center_indx - 10 - 5 * n_clicks_left)]):(center_indx + 10 + 5 * n_clicks_right)
        ]
        xmin = timestamp_range[0].strftime("%Y-%m-%dT%H:%M:%S")
        xmax = timestamp_range[-1].strftime("%Y-%m-%dT%H:%M:%S")
        return xmin, xmax


def layout(user_selected_timestamp, study_agent):
    return html.Div(id="micro_page", children=[
        dcc.Store(id="relayoutStoreMicro"),
        dcc.Store(id="window", data=compute_window(
            user_selected_timestamp, study_agent)),
        indicator_line,
        # TODO : episode.observations[1] will change
        flux_inspector_line(get_network_graph(make_network(episode), episode)),
        context_inspector_line,
        all_info_line
    ])
