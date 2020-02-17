import dash_html_components as html
import dash_core_components as dcc
import dash_antd_components as dac
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import dash_table as dt
import pandas as pd
import numpy as np
import datetime
from collections import namedtuple

from src.grid2kpi.episode_analytics import EpisodeTrace
from src.grid2kpi.episode_analytics import observation_model
from src.grid2kpi.manager import (
    episode, make_episode, base_dir, episode_name, make_network, get_network_graph)

layout_def = {
    'legend': {'orientation': 'h'},
    "showlegend": True,
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

SliderParams = namedtuple("SliderParams", ['min', 'max', 'marks', 'value'])


def indicator_line(reward_graph, actions_ts_graph):
    return html.Div(id="indicator_line_id", className="lineBlock card", children=[
        html.H4("Indicators"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-xl-6", children=[
                html.H6(className="text-center",
                        children="Rewards instant + cumulated for 2 agent"),
                dcc.Graph(
                    id="cum_instant_reward_ts",
                    figure=reward_graph
                )
            ]),

            html.Div(className="col-xl-6", children=[
                html.H6(className="text-center",
                        children="Actions"),
                dcc.Graph(
                    id="actions_ts",
                    figure=actions_ts_graph
                )
            ])
        ])
    ])


def flux_inspector_line(network_graph=None, slider_params=None):
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
                        ),
                        dcc.Slider(
                            id="slider",
                            min=slider_params.min,
                            max=slider_params.max,
                            step=None,
                            marks=slider_params.marks,
                            value=slider_params.value
                        )
                    ])
                ]),
                html.Div(className="row", children=[
                    html.Div(className="col", children=[
                        html.H6(className="text-center",
                                children="Voltage and Flow"),
                        dac.Radio(options=[
                            {'label': 'Voltage', 'value': 'voltage'},
                            {'label': 'Flow', 'value': 'flow'}
                        ],
                            value="voltage",
                            id="voltage_flow_choice",
                            buttonStyle="solid"
                        ),
                        dac.Radio(options=[
                            {'label': 'Active Flow', "value": "active_flow"},
                            {'label': 'Current Flow', 'value': 'current_flow'},
                            {'label': 'Flow Usage Rate', 'value': 'flow_usage_rate'}
                        ],
                            value='active_flow',
                            id='flow_radio',
                            style={'display': 'none'}
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
                        data=episode.usage_rate_trace
                    ),
                    config=dict(displayModeBar=False)
                ),
                dcc.Graph(
                    id='overflow_ts',
                    className="col-6",
                    style={'margin-top': '1em'},
                    figure=go.Figure(
                        layout=layout_def,
                        data=episode.total_overflow_trace
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


def center_index(user_selected_timestamp, episode):
    if user_selected_timestamp is not None:
        center_indx = episode.timestamps.index(
            datetime.datetime.strptime(
                user_selected_timestamp, '%Y-%m-%d %H:%M')
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
    timestamp_range = episode.timestamps[
                      min_:max_
                      ]
    marks = dict(zip(range(min_, max_), timestamp_range))
    return SliderParams(min_, max_, marks, value)


def compute_window(user_selected_timestamp, study_agent):
    if user_selected_timestamp is not None:
        n_clicks_left = 0
        n_clicks_right = 0
        new_episode = make_episode(study_agent, episode_name)
        center_indx = center_index(user_selected_timestamp, new_episode)
        timestamp_range = new_episode.timestamps[
                          max([0, (center_indx - 10 - 5 * n_clicks_left)]):(center_indx + 10 + 5 * n_clicks_right)
                          ]
        xmin = timestamp_range[0].strftime("%Y-%m-%dT%H:%M:%S")
        xmax = timestamp_range[-1].strftime("%Y-%m-%dT%H:%M:%S")
        return xmin, xmax


def reward_graph(user_selected_timestamp, base_dir, study_agent, episode_name, agent_ref):
    new_episode = make_episode(study_agent, episode_name)
    ref_episode = make_episode(agent_ref, episode_name)
    actions_ts = new_episode.action_data.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    figure = {}
    df = observation_model.get_df_computed_reward(new_episode)
    action_events_df = pd.DataFrame(
        index=df["timestep"], data=np.nan, columns=["action_events"])
    action_events_df.loc[(actions_ts["Nb Actions"] > 0).values, "action_events"] = \
        df.loc[(actions_ts["Nb Actions"] > 0).values, "rewards"].values
    action_trace = go.Scatter(
        x=action_events_df.index, y=action_events_df["action_events"], name="Actions",
        mode='markers', marker_color='#FFEB3B',
        marker={"symbol": "hexagon", "size": 10}
    )
    ref_episode_reward_trace = ref_episode.reward_trace
    studied_agent_reward_trace = make_episode(study_agent, episode_name).reward_trace

    figure['data'] = [*ref_episode_reward_trace, *studied_agent_reward_trace,
                      action_trace]
    figure['layout'] = {**layout_def,
                        'yaxis2': {'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }

    window = compute_window(user_selected_timestamp, study_agent)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )
    return figure


from src.grid2viz.micro.micro_clbk import action_tooltip


def actions_ts_graph(user_selected_timestamp, base_dir, study_agent, episode_name, agent_ref):
    new_episode = make_episode(study_agent, episode_name)
    actions_ts = new_episode.action_data.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    ref_episode = make_episode(agent_ref, episode_name)
    ref_agent_actions_ts = ref_episode.action_data.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    figure = {}
    figure["data"] = [
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=actions_ts["Nb Actions"], name=study_agent,
                   text=action_tooltip(new_episode.actions)),
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=ref_agent_actions_ts["Nb Actions"], name=agent_ref,
                   text=action_tooltip(ref_episode.actions)),

        go.Scatter(x=new_episode.action_data.timestamp,
                   y=new_episode.action_data["distance"], name=study_agent + " distance", yaxis='y2'),
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=ref_episode.action_data["distance"], name=agent_ref + " distance", yaxis='y2'),
    ]
    figure['layout'] = {**layout_def,
                        'yaxis2': {'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }

    window = compute_window(user_selected_timestamp, study_agent)

    if window is not None:
        figure["layout"].update(
            xaxis=dict(range=window, autorange=False)
        )

    return figure


def layout(user_selected_timestamp, study_agent, ref_agent):
    new_episode = make_episode(study_agent, episode_name)
    center_indx = center_index(user_selected_timestamp, new_episode)
    centered_date = new_episode.timestamps[center_indx]
    network_graph = make_network(new_episode).get_plot_observation(new_episode.observations[center_indx])
    rw_graph = reward_graph(user_selected_timestamp, base_dir, study_agent, episode_name, ref_agent)
    act_graph = actions_ts_graph(user_selected_timestamp, base_dir, study_agent, episode_name, ref_agent)
    return html.Div(id="micro_page", children=[
        dcc.Store(id="relayoutStoreMicro"),
        dcc.Store(id="window", data=compute_window(
            user_selected_timestamp, study_agent)),
        indicator_line(rw_graph, act_graph),
        # TODO : episode.observations[1] will change
        flux_inspector_line(network_graph, slider_params(user_selected_timestamp, new_episode)),
        # flux_inspector_line(get_network_graph(make_network(episode), episode)),
        context_inspector_line,
        all_info_line
    ])
