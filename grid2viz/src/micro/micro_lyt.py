import dash_html_components as html
import dash_core_components as dcc
import dash_antd_components as dac
import plotly.graph_objects as go
import dash_table as dt
import datetime
from collections import namedtuple

from grid2viz.src.manager import make_episode, make_network, best_agents
from grid2viz.src.utils import common_graph

layout_def = {
    'legend': {'orientation': 'h'},
    'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
}

SliderParams = namedtuple("SliderParams", ['min', 'max', 'marks', 'value'])


def indicator_line():
    return html.Div(id="indicator_line_id", className="lineBlock card", children=[
        html.H4("Indicators"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-6", children=[
                html.H6(className="text-center",
                        children="Rewards instant + cumulated for 2 agent"),
                dcc.Graph(
                    id="cum_instant_reward_ts",
                    figure=go.Figure(
                        layout=layout_def,
                    )
                )
            ]),

            html.Div(className="col-6", children=[
                html.H6(className="text-center",
                        children="Actions"),
                dcc.Graph(
                    id="actions_ts",
                    figure=go.Figure(
                        layout=layout_def,
                    )
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
                            {'label': 'Voltage (V)', 'value': 'voltage'},
                            {'label': 'Flow', 'value': 'flow'}
                        ],
                            value="voltage",
                            id="voltage_flow_choice",
                            buttonStyle="solid"
                        ),
                        dac.Radio(options=[
                            {'label': 'Active Flow (MW)',
                             "value": "active_flow"},
                            {'label': 'Current Flow (A)',
                             'value': 'current_flow'},
                            {'label': 'Flow Usage Rate',
                             'value': 'flow_usage_rate'}
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


def context_inspector_line(best_episode, study_episode):
    return html.Div(id="context_inspector_line_id", className="lineBlock card ", children=[
        html.H4("Context"),
        html.Div(className="card-body col row", children=[

            html.Div(className="col-xl-5", children=[
                html.H5("Best Agent's Environment Time Series"),
                dcc.RadioItems(options=[
                    {'label': 'Load', "value": "Load"},
                    {'label': 'Production', "value": "Production"},
                    {'label': 'Hazards', "value": "Hazards"},
                    {'label': 'Maintenances', "value": "Maintenances"},
                ],
                    value="Load",
                    id="environment_choices_buttons"
                ),
                dac.Select(
                    id='asset_selector',
                    options=[{'label': load_name,
                              'value': load_name}
                             for load_name in best_episode.load_names],
                    value=best_episode.load_names[0],
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

                html.Div(className="row", children=[
                    html.Div(className='col-6', children=[
                        html.H5("Usage rate", className='text-center'),
                        dcc.Graph(
                            id='usage_rate_ts',
                            style={'margin-top': '1em'},
                            figure=go.Figure(
                                layout=layout_def,
                                data=study_episode.usage_rate_trace
                            ),
                            config=dict(displayModeBar=False)
                        )
                    ]),
                    html.Div(className='col-6', children=[
                        html.H5("Overflow", className='text-center'),
                        dcc.Graph(
                            id='overflow_ts',
                            style={'margin-top': '1em'},
                            figure=go.Figure(
                                layout=layout_def,
                                data=study_episode.total_overflow_trace
                            ),
                            config=dict(displayModeBar=False)
                        ),
                    ])
                ]),
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
    timestamp_range = [timestamp.time() for timestamp in timestamp_range]
    marks = dict(enumerate(timestamp_range))
    return SliderParams(min_, max_, marks, value)


def compute_window(user_selected_timestamp, study_agent, scenario):
    if user_selected_timestamp is not None:
        n_clicks_left = 0
        n_clicks_right = 0
        new_episode = make_episode(study_agent, scenario)
        center_indx = center_index(user_selected_timestamp, new_episode)

        return common_graph.compute_windows_range(
            new_episode, center_indx, n_clicks_left, n_clicks_right
        )


def layout(user_selected_timestamp, study_agent, ref_agent, scenario):
    best_episode = make_episode(best_agents[scenario]["agent"], scenario)
    new_episode = make_episode(study_agent, scenario)
    center_indx = center_index(user_selected_timestamp, new_episode)
    network_graph = make_network(new_episode).get_plot_observation(new_episode.observations[center_indx])

    return html.Div(id="micro_page", children=[
        dcc.Store(id="window", data=compute_window(user_selected_timestamp, study_agent, scenario)),
        indicator_line(),
        flux_inspector_line(network_graph, slider_params(user_selected_timestamp, new_episode)),
        context_inspector_line(best_episode, new_episode),
        all_info_line
    ])
