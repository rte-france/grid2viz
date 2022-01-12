import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import datetime as dt
from grid2viz.src.manager import make_episode, make_network_agent_study


def lines_tab_layout(episode):
    return [
        html.P("Choose a line to act on:", className="my-2"),
        dac.Select(
            id="select_lines_simulation",
            options=[
                {"label": line_name, "value": line_name}
                for line_name in episode.line_names
            ],
            mode="default",
            value=episode.line_names[0],
        ),
        html.P("Choose an action type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_lines",
            buttonStyle="solid",
        ),
        html.P("Choose a target type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Status", "value": "Status"},
                {"label": "Bus", "value": "Bus"},
            ],
            value="Status",
            id="radio_target_lines",
            buttonStyle="solid",
        ),
        dac.Radio(
            options=[
                {"label": "Disconnect", "value": "Disconnect"},
                {"label": "Bus 1", "value": "Bus1"},
                {"label": "Bus 2", "value": "Bus2"},
            ],
            value="Disconnect",
            id="radio_bus_lines",
            buttonStyle="solid",
            className="hidden",
        ),
        dac.Radio(
            options=[
                {"label": "Origin", "value": "Origin"},
                {"label": "Extremity", "value": "Extremity"},
            ],
            value="Origin",
            id="radio_ex_or_lines",
            buttonStyle="solid",
            className="hidden",
        ),
        dac.Radio(
            options=[
                {"label": "Reconnect", "value": "Reconnect"},
                {"label": "Disconnect", "value": "Disconnect"},
            ],
            value="Reconnect",
            id="radio_disc_rec_lines",
            buttonStyle="solid",
            className="mt-1",
        ),
    ]


def loads_tab_layout(episode):
    return [
        html.P("Choose a Load to act on:"),
        dac.Select(
            id="select_loads_simulation",
            options=[{"label": name, "value": name} for name in episode.load_names],
            mode="default",
            value=episode.load_names[0],
        ),
        html.P("Choose an action type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_loads",
            buttonStyle="solid",
        ),
        html.P("Choose an action:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Disconnect", "value": "Disconnect"},
                {"label": "Bus 1", "value": "Bus1"},
                {"label": "Bus 2", "value": "Bus2"},
            ],
            value="Disconnect",
            id="radio_bus_loads",
            buttonStyle="solid",
            className="mt-1",
        ),
    ]


def gens_tab_layout(episode):
    return [
        html.P("Choose a generator to act on:"),
        dac.Select(
            id="select_gens_simulation",
            options=[
                {"label": prod_name, "value": prod_name}
                for prod_name in episode.prod_names
            ],
            mode="default",
            value=episode.prod_names[0],
        ),
        html.P("Choose an action type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Redispatch", "value": "Redispatch"},
                {"label": "Topology", "value": "Topology"},
            ],
            value="Redispatch",
            id="radio_action_type_gens",
            buttonStyle="solid",
        ),
        dcc.Input(
            id="input_redispatch", type="number", placeholder="MW", className="mt-1"
        ),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_gens",
            buttonStyle="solid",
            className="hidden",
        ),
        dac.Radio(
            options=[
                {"label": "Disconnect", "value": "Disconnect"},
                {"label": "Bus 1", "value": "Bus1"},
                {"label": "Bus 2", "value": "Bus2"},
            ],
            value="Disconnect",
            id="radio_bus_gens",
            buttonStyle="solid",
            className="hidden",
        ),
    ]


def choose_tab_content(episode):
    return html.Div(
        [
            dbc.Tabs(
                id="tab_method",
                className="nav-fill",
                children=[
                    dbc.Tab(
                        tab_id="tab_method_dropdowns",
                        label="Dropdowns",
                        children=[
                            dbc.Tabs(
                                id="tab_object",
                                className="nav-fill",
                                children=[
                                    dbc.Tab(
                                        tab_id="tab_object_lines",
                                        label="Lines",
                                        children=lines_tab_layout(episode),
                                    ),
                                    dbc.Tab(
                                        tab_id="tab_object_loads",
                                        label="Loads",
                                        children=loads_tab_layout(episode),
                                    ),
                                    dbc.Tab(
                                        tab_id="tab_object_gens",
                                        label="Gens",
                                        children=gens_tab_layout(episode),
                                    ),
                                ],
                            )
                        ],
                    ),
                    dbc.Tab(
                        tab_id="tab_method_dict",
                        label="Dict",
                        children=[
                            html.P("Enter the action dictionary:"),
                            dbc.Textarea(
                                id="textarea",
                                className="mb-3",
                                placeholder='{"set_line_status": []}',
                            ),
                        ],
                    ),
                ],
            ),
            dbc.Button(
                "Add",
                id="add_action",
                color="danger",
                className="mt-3 mb-3",
            ),
            dbc.Button(
                "Reset",
                id="reset_action",
                color="secondary",
                className="m-3",
            ),
            html.P(
                id="action_info",
                className="more-info-table",
                children="Compose some actions to study",
            ),
        ]
    )


def choose_assist_line(network_graph):
    return html.Div(
        id="choose_assist_line",
        className="lineBlock card",
        children=[
            html.H4("Choose or Assist"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        id="div-choose-assist",
                        className="col-7 chooseAssist",
                        children=[
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        dbc.Tabs(
                                            id="tabs-choose-assist-method",
                                            card=True,
                                            active_tab="tab-choose-method",
                                            children=[
                                                dbc.Tab(
                                                    label="Choose",
                                                    tab_id="tab-choose-method",
                                                ),
                                                dbc.Tab(
                                                    label="Assist",
                                                    tab_id="tab-assist-method",
                                                ),
                                            ],
                                        )
                                    ),
                                    dbc.CardBody(
                                        html.Div(id="tabs-choose-assist-method-content")
                                    ),
                                ]
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-5",
                        id="div-network-graph-choose-assist",
                        children=[
                            html.H5("Network at time step t"),
                            html.Div(
                                id="graph_div",
                                children=[
                                    dcc.Graph(
                                        id="network_graph_choose",
                                        figure=network_graph,
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def compare_line(episode, timestep):
    timestamp = episode.timestamps[timestep]
    reward = f"{episode.rewards[timestep]:,.0f}"
    rho = f"{episode.rho.loc[ episode.rho.timestamp == timestamp, 'value'].max() * 100:.0f}%"
    nb_overflows = f"{episode.total_overflow_ts['value'][timestep]:,.0f}"
    losses = f"0"
    return html.Div(
        id="compare_line",
        className="lineBlock card",
        children=[
            html.H4("Compare"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col-3",
                        children=[
                            html.Div(
                                className="row",
                                children=[
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H5("Agent's KPIs"),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="agent_reward",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children=reward,
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="Agent's reward",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="agent_rho",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children=rho,
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="Agent's max rho",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="agent_overflows",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children=nb_overflows,
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="Agent's overflows",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="agent_losses",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children=losses,
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="Agent's losses",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        className="col-6",
                                        children=[
                                            html.H5("New Action's KPIs"),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="new_action_reward",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children="0",
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="New Action reward",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="new_action_rho",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children="0",
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="New Action max rho",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="new_action_overflows",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children="0",
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="New Action overflows",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="mb-4",
                                                children=[
                                                    html.P(
                                                        id="new_action_losses",
                                                        className="border-bottom h3 mb-0 text-right",
                                                        children="0",
                                                    ),
                                                    html.P(
                                                        className="text-muted",
                                                        children="New Action losses",
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                    html.Div(
                        className="col-9",
                        children=[
                            html.Div(
                                className="row",
                                children=[
                                    dbc.Button(
                                        "Simulate",
                                        id="simulate_action",
                                        color="primary",
                                        className="btn-block mx-3",
                                    ),
                                ],
                            ),
                            html.Div(
                                children=[
                                    dbc.Card(
                                        [
                                            dbc.CardHeader(
                                                dbc.Tabs(
                                                    id="tabs_network",
                                                    children=[
                                                        dbc.Tab(
                                                            label="New State",
                                                            tab_id="tab_new_network_state",
                                                        ),
                                                        # dbc.Tab(
                                                        #     label="Old State t+1",
                                                        #     tab_id="tab_old_network_state",
                                                        # ),
                                                    ],
                                                    active_tab="tab_new_network_state",
                                                ),
                                            ),
                                            dbc.CardBody(
                                                id="card_body_network",
                                                children=[
                                                    "Compose an action above and then simulate it."
                                                ],
                                            ),
                                        ]
                                    )
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


def layout(study_agent, scenario, user_timestep=None):
    episode = make_episode(study_agent, scenario,with_reboot=True)
    if user_timestep is None:
        user_timestep = 1
    network_graph = make_network_agent_study(
        episode, timestep=user_timestep, responsive=True
    )
    return html.Div(
        id="simulation_page",
        children=[
            dcc.Store(id="actions", storage_type="memory"),
            dcc.Store(id="simulation-assistant-store", storage_type="memory"),
            dcc.Store(id="simulation-assistant-size", storage_type="memory"),
            dcc.Store(id="network_graph_t", storage_type="memory", data=network_graph),
            dcc.Store(
                id="network_graph_new",
                storage_type="memory",
            ),
            choose_assist_line(network_graph),
            compare_line(episode, timestep=user_timestep),
        ],
    )
