import dash_core_components as dcc
import dash_html_components as html
import dash_antd_components as dac

from grid2viz.src.manager import (agent_scenario, make_network, make_episode)


def choose_line(network_graph):
    return html.Div(id="choose_line", className="lineBlock card", children=[
        html.H4("Choose or Assist"),
        html.Div(className="card-body row", children=[
            html.Div(className="col-9", children=[
                html.H5("Network at time step t"),
                dcc.Graph(id="network_graph_choose", figure=network_graph),
            ]),
            html.Div(className="col-3", children=[
                "content"
            ])
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


def assist_line():
    return html.Div(id="assist_line", className="lineBlock card", children=[
        html.H4("Assist"),
        html.Div(className="card-body row", children="Content"),
    ])


def layout(scenario, studied_agent):
    episode = make_episode(studied_agent, scenario)
    # TODO : center en correct time step
    network_graph = make_network(episode).plot_obs(
        observation=episode.observations[0]
    )
    return html.Div(id="simulation_page", children=[
        choose_line(network_graph),
        compare_line(network_graph),
        assist_line()
    ])
