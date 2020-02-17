from dash.dependencies import Input, Output, State
from dash import callback_context
from grid2kpi.episode_analytics import EpisodeTrace
from src.app import app
from src.grid2kpi.episode_analytics.consumption_profiles import profiles_traces
from src.grid2kpi.manager import scenarios, best_agents, meta_json, make_episode, prod_types
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from src.grid2viz.utils.perf_analyser import whoami, timeit


@app.callback(
    Output('cards_container', 'children'),
    [Input('url', 'pathname')]
)
def load_scenario_cards(url):
    cards_list = []
    cards_count = 0
    episode_graph_layout = {
        'autosize': True,
        'showlegend': False,
        'xaxis': {'showticklabels': False},
        'yaxis': {'showticklabels': False},
        'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
    }
    if cards_count < 15:
        for scenario in sorted(scenarios):
            best_agent_episode = make_episode(best_agents[scenario]['agent'], scenario)
            prod_share = EpisodeTrace.get_prod_share_trace(best_agent_episode, prod_types)
            consumption = profiles_traces(best_agent_episode, freq="30T")

            cards_list.append(
                dbc.Col(lg=4, width=12, children=[
                    dbc.Card(className='mb-3', children=[
                        dbc.CardBody([
                            html.H5(className="card-title",
                                    children="Scenario {0}".format(scenario)),
                            dbc.Row(children=[
                                dbc.Col(className="mb-4", children=[
                                    html.P(className="border-bottom h3 mb-0 text-right",
                                           children=best_agents[scenario]['out_of']),
                                    html.P(className="text-muted", children="Agents on Scenario")
                                ]),
                                dbc.Col(className="mb-4", children=[
                                    html.P(className="border-bottom h3 mb-0 text-right",
                                           children='{}/{}'.format(best_agents[scenario]['value'], meta_json[scenario]['chronics_max_timestep'])),
                                    html.P(className="text-muted", children="Agent's Survival")
                                ]),
                                dbc.Col(className="mb-4", children=[
                                    html.P(className="border-bottom h3 mb-0 text-right",
                                           children=round(best_agents[scenario]['cum_reward'])),
                                    html.P(className="text-muted", children="Cumulative Reward")
                                ]),
                            ]),
                            dbc.Row(className="align-items-center", children=[
                                dbc.Col(lg=4, width=12, children=[
                                    html.H5('Production Share',  className='text-center'),
                                    dcc.Graph(
                                        style={'height': '150px'},
                                        figure=go.Figure(
                                            layout=episode_graph_layout,
                                            data=prod_share,
                                        )
                                    )
                                ]),
                                dbc.Col(lg=8, width=12, children=[
                                    html.H5('Consumption Profile', className='text-center'),
                                    dcc.Graph(
                                        style={'height': '150px'},
                                        figure=go.Figure(
                                            layout=episode_graph_layout,
                                            data=consumption
                                        ))
                                    ]
                                )
                            ])
                        ]),
                        dbc.CardFooter(dbc.Button(
                            "Open", id=scenario, key=scenario,
                            className="btn-block",
                            style={"background-color": "#2196F3"}))
                    ])
                ])
            )
            cards_count += 1
    return cards_list


@app.callback(
    [Output('scenario', 'data'), Output('url', 'pathname')],
    [Input(scenario, 'n_clicks') for scenario in scenarios],
    [State(scenario, 'key') for scenario in scenarios]
)
def open_scenario(*input_state):
    # use callback context to get triggered input then parse it to get triggered input id
    # finaly get the state key value from context with the dict key = input_id + .key
    # see : https://dash.plot.ly/faqs How do I determine which Input has changed?

    ctx = callback_context
    input_id = ctx.triggered[0]['prop_id'].split('.')[0]
    input_key = ctx.states[input_id + '.key']
    scenario = input_key

    return scenario, '/overview'
