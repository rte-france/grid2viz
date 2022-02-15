# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import datetime
from collections import namedtuple
from pathlib import Path

import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_table as dt
import plotly.graph_objects as go

from grid2viz.src.manager import grid2viz_home_directory
from grid2viz.src.manager import make_episode, make_network_agent_study, best_agents
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.layout_helpers import modal, should_help_open

layout_def = {
    "legend": {"orientation": "h"},
    "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
}

SliderParams = namedtuple("SliderParams", ["min", "max", "marks", "value"])


def indicator_line():
    return html.Div(
        id="indicator_line_id",
        className="lineBlock card",
        children=[
            html.H4("Indicators"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col-6",
                        children=[
                            html.H6(
                                className="text-center",
                                children="Rewards instant + cumulated for 2 agent",
                            ),
                            dbc.Tabs(
                                children=[
                                    dbc.Tab(
                                        label="Instant Reward",
                                        children=[
                                            dcc.Graph(
                                                id="rewards_ts",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                ),
                                            )
                                        ],
                                    ),
                                    dbc.Tab(
                                        label="Cumulated Reward",
                                        children=[
                                            dcc.Graph(
                                                id="cumulated_rewards_ts",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                ),
                                            )
                                        ],
                                    ),
                                ]
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-6",
                        children=[
                            html.H6(
                                className="text-center",
                                children="Distance from reference grid configuration",
                            ),
                            dcc.Graph(
                                id="actions_ts",
                                figure=go.Figure(
                                    layout=layout_def, data=[dict(type="scatter")]
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def card_for_network_graphs(network_graph):
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Tabs(
                    [
                        dbc.Tab(label="Study Agent", tab_id="tab-0"),
                        dbc.Tab(label="Reference Agent", tab_id="tab-1"),
                    ],
                    id="card-tabs",
                    card=True,
                    active_tab="tab-0",
                )
            ),
            dbc.CardBody(
                id="card-content",
                children=[
                    dcc.Graph(
                        id="interactive_graph",
                        figure=dict(dict(data=network_graph["data"],layout=network_graph["layout"])),#network_graph,
                    ),
                    #dcc.Interval(id='auto-stepper', interval=1000, n_intervals=0),
                    #dcc.Store(id='offset', data=0), dcc.Store(id='store', data=network_graph["data"])
                ],
            ),
        ]
    )


def flux_inspector_line(network_graph=None, slider_params=None):
    return html.Div(
        id="flux_inspector_line_id",
        className="lineBlock card",
        children=[
            html.H4("State evolution given agent actions"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col",
                        children=[
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Grid State evolution overtime & highlighted subs with action (yellow) - with 2 nodes (green) ",
                                            ),
                                            card_for_network_graphs(network_graph),

                                            #daq.ToggleSwitch(
                                            #    id="toggle",
                                            #    velue=False#,
                                            #    #label='Animate',
                                            #    #labelPosition='bottom'
                                            #),
                                            html.Div(
                                                className="row",
                                                children=[
                                                    html.Div(
                                                        className="col-1",
                                                        children=[
                                                                daq.PowerButton(
                                                                    id='my-toggle-switch',
                                                                    on=False,#,
                                                                    label='Power On for Auto',
                                                                    disabled=False
                                                                ),
                                                                html.Div(id='my-toggle-switch-output'),
                                                            ],
                                                    ),
                                                    html.Div(
                                                        className="col-10",
                                                        children=[
                                                            dcc.Slider(
                                                                id="slider",
                                                                min=slider_params.min,
                                                                max=slider_params.max,
                                                                step=None,
                                                                marks=slider_params.marks,
                                                                value=slider_params.value,
                                                                disabled=False
                                                            ),
                                                            ],
                                                    ),
                                                    dcc.Interval(id='auto-stepper', interval=3000000, n_intervals=0),#,disabled=True),
                                                ],
                                            ),
                                            html.P(
                                                id="tooltip_table_micro",
                                                className="more-info-table",
                                                children=[
                                                    "Click on a row to have more info on the action"
                                                ],
                                            ),
                                        ],
                                    )
                                ],
                            ),
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col",
                                        children=[
                                            html.H6(
                                                className="text-center",
                                                children="Voltage, Flow and Redispatch time series",
                                            ),
                                            dac.Radio(
                                                options=[
                                                    {"label": "Flow", "value": "flow"},
                                                    {
                                                        "label": "Voltage (V)",
                                                        "value": "voltage",
                                                    },
                                                    {
                                                        "label": "Redispatch (MW)",
                                                        "value": "redispatch",
                                                    },
                                                ],
                                                value="flow",
                                                id="voltage_flow_choice",
                                                buttonStyle="solid",
                                            ),
                                            dac.Radio(
                                                options=[
                                                    {
                                                        "label": "Active Flow (MW)",
                                                        "value": "active_flow",
                                                    },
                                                    {
                                                        "label": "Current Flow (A)",
                                                        "value": "current_flow",
                                                    },
                                                    {
                                                        "label": "Flow Usage Rate",
                                                        "value": "flow_usage_rate",
                                                    },
                                                ],
                                                value="active_flow",
                                                id="flow_radio",
                                                style={"display": "none"},
                                            ),
                                            dac.Select(
                                                id="line_side_choices",
                                                options=[],
                                                value=[],
                                                mode="multiple",
                                                showArrow=True,
                                            ),
                                            dcc.Graph(
                                                id="voltage_flow_graph",
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=[dict(type="scatter")],
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


def context_inspector_line(best_episode, study_episode):
    return html.Div(
        id="context_inspector_line_id",
        className="lineBlock card ",
        children=[
            html.H4("Context"),
            html.Div(
                className="card-body col row",
                children=[
                    html.Div(
                        className="col-xl-5",
                        children=[
                            html.H5("Environment Time Series"),
                            dac.Radio(
                                options=[
                                    {"label": "Production", "value": "Production"},
                                    {"label": "Load", "value": "Load"},
                                    {"label": "Hazards", "value": "Hazards"},
                                    {"label": "Maintenances", "value": "Maintenances"},
                                ],
                                value="Production",
                                id="environment_choices_buttons",
                                buttonStyle="solid",
                            ),
                            dac.Select(
                                id="asset_selector",
                                options=[
                                    {"label": prod_name, "value": prod_name}
                                    for prod_name in best_episode.prod_names
                                ],
                                value="solar",
                                # episode.prod_names[3],#[episode.prod_names[0],episode.prod_names[1]],#[prod_name for prod_name in episode.prod_names if prod_name in ['wind','solar']],#episode.prod_names[0]
                                mode="multiple",
                                showArrow=True,
                            ),
                            dcc.Graph(
                                id="env_charts_ts",
                                style={"margin-top": "1em"},
                                figure=go.Figure(
                                    layout=layout_def, data=[dict(type="scatter")]
                                ),
                                config=dict(displayModeBar=False),
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-xl-7",
                        children=[
                            html.H5("Studied agent Metrics"),
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H5(
                                                "Usage rate", className="text-center"
                                            ),
                                            dcc.Graph(
                                                id="usage_rate_ts",
                                                style={"margin-top": "1em"},
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=study_episode.usage_rate_trace,
                                                ),
                                                config=dict(displayModeBar=False),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H5(
                                                "Overflow", className="text-center"
                                            ),
                                            dcc.Graph(
                                                id="overflow_ts",
                                                style={"margin-top": "1em"},
                                                figure=go.Figure(
                                                    layout=layout_def,
                                                    data=study_episode.total_overflow_trace,
                                                ),
                                                config=dict(displayModeBar=False),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


all_info_line = html.Div(
    id="all_info_line_id",
    className="lineBlock card ",
    children=[
        html.H4("All"),
        html.Div(
            className="card-body col row",
            children=[
                html.Div(
                    className="col-xl-10",
                    children=[
                        dt.DataTable(
                            id="all_info_table",
                            filter_action="native",
                            sort_action="native",
                            sort_mode="multi",
                            page_action="native",
                            page_current=0,
                            page_size=20,
                        )
                    ],
                )
            ],
        ),
    ],
)




def center_index(user_selected_timestamp, episode):
    if user_selected_timestamp is not None:
        center_indx = episode.timestamps.index(
            datetime.datetime.strptime(user_selected_timestamp, "%Y-%m-%d %H:%M")
        )
    else:
        center_indx = 0
    return center_indx


def slider_params(user_selected_timestamp, episode):
    # min max marks value
    value = center_index(user_selected_timestamp, episode)
    n_clicks_left = 0
    n_clicks_right = 0
    min_ = max([0, (value - 10 - 5 * n_clicks_left)])
    max_ = min([(value + 10 + 5 * n_clicks_right), len(episode.timestamps)])
    timestamp_range = episode.timestamps[min_:(max_+1)]
    timestamp_range = [timestamp.time() for timestamp in timestamp_range]
    if ("is_action" in episode.action_data_table.columns):
        is_actions = list(episode.action_data_table.is_action[min_:(max_ + 1)].values)

        marks = {int(min_ + idx): {'label': t, 'style': {'color': 'orange'}} if is_act else {'label': t, 'style': {
            'color': 'black'}} for idx, (t, is_act) in enumerate(zip(timestamp_range, is_actions))}

        if ("is_alarm" in episode.action_data_table.columns):
            is_alarm = list(episode.action_data_table.is_alarm[min_:(max_ + 1)].values)
            for idx, mark_key in enumerate(marks.keys()):
                if is_alarm[idx]:
                    marks[mark_key]['style']['background-color'] = 'lightcoral'
    else:
        marks = {int(min_ + idx): {'label': t, 'style': {'color': 'black'}} for idx, t in enumerate(timestamp_range)}

    return SliderParams(min_, max_, marks, value)


def layout(user_selected_timestamp, study_agent, ref_agent, scenario):
    best_episode = make_episode(best_agents[scenario]["agent"], scenario)
    new_episode = make_episode(study_agent, scenario)
    center_indx = center_index(user_selected_timestamp, new_episode)
    network_graph = make_network_agent_study(new_episode, timestep=center_indx)

    open_help = should_help_open(
        Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("micro")
    )
    header = "Analyze further your agent"
    body = (
        "Select a time step in the navbar dropdown and analyze what happened "
        "at that time to understand the agent behavior."
    )
    return html.Div(
        id="micro_page",
        children=[
            indicator_line(),
            flux_inspector_line(
                network_graph,
                slider_params(user_selected_timestamp, new_episode),
            ),
            context_inspector_line(best_episode, new_episode),
            all_info_line,
            modal(id_suffix="micro", is_open=open_help, header=header, body=body),
        ],
    )
