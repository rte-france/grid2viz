import dash_html_components as html
import dash_core_components as dcc
import dash_antd_components as dac
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd
import numpy as np

from src.grid2kpi.episode import observation_model
from src.grid2kpi.manager import episode, agents, agent_ref

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
            dcc.Loading(
                dcc.Graph(
                    id="cum_instant_reward_ts",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="bar")]
                    )
                )
            )
        ]),

        html.Div(className="col-xl-6", children=[
            html.H6(className="text-center",
                    children="Actions"),
            dcc.Loading(
                dcc.Graph(
                    id="actions_ts",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="bar")]
                    )
                ))
        ])
    ])
])

flux_inspector_line = html.Div(id="flux_inspector_line_id", className="lineBlock card", children=[
    html.H4("Flux"),
    html.Div(className="card-body row", children=[

        html.Div(className="col-xl-4", children=[
            html.H6(className="text-center",
                    children="Interactive Graph"),

            dcc.Loading(
                dcc.Graph(
                    id="interactive_graph",
                    figure=go.Figure(
                        layout=layout_def,
                    )
                )
            )
        ]),
        html.Div(className="col-xl-8", children=[
            html.H6(className="text-center",
                    children="Title"),
            dac.Radio(options=[
                {'label': 'Voltage', "value": "voltage"},
                {'label': 'Flow', "value": "flow"},
            ],
                value="voltage",
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
            dcc.Loading(
                dcc.Graph(
                    id="voltage_flow_graph",
                    figure=go.Figure(
                        layout=layout_def,
                        data=[dict(type="scatter")]
                    )
                ))
        ]),
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
            dcc.Dropdown(
                id="agent_selector", placeholder="select a ref agent",
                options=[{'label': agent, 'value': agent} for agent in agents],
                value=agent_ref
            ),
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

layout = html.Div(id="micro_page", children=[
    dcc.Store(id="relayoutStoreMicro"),
    indicator_line,
    flux_inspector_line,
    context_inspector_line,
    all_info_line
])
