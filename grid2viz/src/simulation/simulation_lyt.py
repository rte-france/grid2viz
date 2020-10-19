import dash_core_components as dcc
import dash_html_components as html
import dash_antd_components as dac
import dash_bootstrap_components as dbc

from grid2viz.src.manager import (agent_scenario, make_network, make_episode)


def choose_assist_line(episode, network_graph):
    return html.Div(id="choose_assist_line", className="lineBlock card", children=[
        html.H4("Choose or Assist"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-7", children=[
                html.H5("Network at time step t"),
                dcc.Graph(id="network_graph_choose", figure=network_graph,),
            ]),
            html.Div(className="col-5", children=[
                dbc.Tabs(children=[
                    dbc.Tab(label='Choose', labelClassName="fas fa-user", children=[
                        dbc.Tabs(children=[
                            dbc.Tab(label="Dropdowns", children=[
                                dbc.Tabs(children=[
                                    dbc.Tab(label='Lines', children=[
                                        html.P("Choose a line to act on:", className="mt-1"),
                                        dac.Select(
                                            id='select_lines_simulation',
                                            options=[{'label': line_name,
                                                      'value': line_name}
                                                     for line_name in episode.line_names],
                                            mode='default',
                                            value=episode.line_names[0]
                                        ),
                                        html.P("Choose an action:", className="mt-1"),
                                        dac.Radio(options=[
                                            {"label": "Set", "value": "Set"},
                                            {"label": "Change", "value": "Change"},
                                        ], value="Set", id="select_action_lines", buttonStyle="solid"),
                                    ]),
                                    dbc.Tab(label='Subs', children=[
                                        html.P("Choose a substation to act on:"),
                                        dac.Select(
                                            id='select_subs_simulation',
                                            options=[{'label': name,
                                                      'value': name}
                                                     for name in episode.name_sub],
                                            mode='default',
                                            value=episode.name_sub[0]
                                        ),
                                        html.P("Choose an action:"),
                                        dac.Radio(options=[
                                            {"label": "Set", "value": "Set"},
                                            {"label": "Change", "value": "Change"},
                                        ], value="Set", id="select_action_subs", buttonStyle="solid"),
                                    ]),
                                    dbc.Tab(label='Gens', children=[
                                        html.P("Choose a generator to act on:"),
                                        dac.Select(
                                            id='select_gens_simulation',
                                            options=[{'label': prod_name,
                                                      'value': prod_name}
                                                     for prod_name in episode.prod_names],
                                            mode='default',
                                            value=episode.prod_names[0]
                                        ),
                                        html.P("Choose an action:"),
                                        dac.Radio(options=[
                                            {"label": "Redispatch", "value": "Redispatch"},
                                        ], value="Redispatch", id="select_action_gens", buttonStyle="solid"),
                                    ])
                                ])
                            ]),
                            dbc.Tab(label="Dict", children=[
                                html.P("Enter the action dictionary:"),
                                dbc.Textarea(className="mb-3", placeholder="{set_line_status: []}"),
                            ])
                        ]),
                    ]),
                    dbc.Tab(label='Assist', labelClassName="fas fa-robot", children=[
                        "content"
                    ]),
                ]),
                dbc.Button("Simulate", id="simulate_action", color="danger", className="mt-3 mb-3"),
                html.P("Action dictionary:"),
                html.Div(id="action_dictionary")
            ]),
        ]),
    ])


def compare_line(network_graph):
    return html.Div(id="compare_line", className="lineBlock card", children=[
        html.H4("Compare"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-9", children=[
                dac.Radio(options=[
                    {"label": "New State t+1", "value": "new"},
                    {"label": "Old State t+1", "value": "old"},
                    {"label": "Delta", "value": "compare"}
                ], value="new", id="compare_states_radio", buttonStyle="solid"),
                dcc.Graph(id="network_graph_compare", figure=network_graph),
            ]),
            html.Div(className="col-3", children=[
                html.H5("Agent's KPIs"),
                html.Div(className="mb-4", children=[
                    html.P(id="agent_reward", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="Agent's reward")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="agent_rho", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="Agent's max rho")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="agent_overflows", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="Agent's overflows")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="agent_losses", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted",
                           children="Agent's losses")
                ]),
                html.H5("New Action's KPIs"),
                html.Div(className="mb-4", children=[
                    html.P(id="new_action_reward", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="New Action reward")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="new_action_rho", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="New Action max rho")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="new_action_overflows", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted", children="New Action overflows")
                ]),
                html.Div(className="mb-4", children=[
                    html.P(id="new_action_losses", className="border-bottom h3 mb-0 text-right",
                           children="0"),
                    html.P(className="text-muted",
                           children="New Action losses")
                ]),
            ]),
        ]),
    ])


def layout(scenario, studied_agent):
    episode = make_episode(studied_agent, scenario)
    # TODO : center en correct time step
    network_graph = make_network(episode).plot_obs(
        observation=episode.observations[0]
    )
    return html.Div(id="simulation_page", children=[
        choose_assist_line(episode, network_graph),
        compare_line(network_graph),
    ])
