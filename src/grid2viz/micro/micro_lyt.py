import dash_html_components as html
import dash_core_components as dcc
import dash_antd_components as dac
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd

from src.grid2kpi.episode import observation_model
from src.grid2kpi.manager import episode, agents, agent_ref

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

indicator_line = html.Div(className="lineBlock card", children=[
    html.H4("Indicators"),
    html.Div(className="card-body row", children=[
        html.Div(
            className="col-xl-2",
            children=[
                dt.DataTable(
                    id="timeseries_table_micro",
                    columns=[{"name": "Timestamps", "id": "Timestamps"}],
                    style_as_list_view=True,
                    row_deletable=False,
                    filter_action="native",
                    sort_action="native"
                )
            ]
        ),
        html.Div(className="col-xl-5", children=[
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

        html.Div(className="col-xl-5", children=[
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

flux_inspector_line = html.Div(id="overview_line_id", className="lineBlock card", children=[
    html.H4("Flux Inspector"),
    html.Div(className="card-body row", children=[

        html.Div(className="col-xl-4", children=[
            html.H6(className="text-center",
                    children="Interactive Graph"),
            dcc.Loading(
                dcc.Graph(
                    id="interractive_graph",
                    figure=go.Figure(
                        layout=layout_def,
                    )
                )
            )
        ]),
        html.Div(className="col-xl-4", children=[
            html.H6(className="text-center",
                    children="Title"),
            dcc.Loading(
                dcc.Graph(
                    id="temp_id_ts",
                    figure=go.Figure(
                        layout=layout_def
                    )
                ))
        ]),
        html.Div(className="col-xl-4", children=[
            html.H6(className="text-center",
                    children="Title"),
            dcc.Loading(
                dcc.Graph(
                    id="temp_id_heatmap",
                    figure=go.Figure(
                        layout=layout_def
                    )
                ))
        ])
    ])
])

context_inspector_line = html.Div(className="lineBlock card ", children=[
    html.H4("Context Inspector"),
    html.Div(className="card-body col row", children=[

        dac.Radio(options=[
            {'label': 'Conso', "value": "conso"},
            {'label': 'Production', "value": "Production"},
            {'label': 'Hazards', "value": "Hazards"},
            {'label': 'Maintenances', "value": "Maintenances"},
        ],
            value="Load",
            # name="scen_overview_ts_switch",
            id="switch_button_context",
            buttonStyle="solid"
        ),
        html.Div(className="col-xl-12", children=[
            html.H6(className="text-center",
                    children="Title"),
            dcc.Loading(
                dcc.Graph(
                    id="temp_id_heatmap",
                    figure=go.Figure(
                        layout=layout_def
                    )
                ))
        ])

    ])
])

all_info_line = html.Div(className="lineBlock card ", children=[
    html.H4("All Informations"),
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
