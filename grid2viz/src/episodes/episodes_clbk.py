# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

from functools import partial
import os
from pathlib import Path
import time

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pathos.multiprocessing import ProcessPool

from grid2viz.src.kpi import EpisodeTrace
from grid2viz.src.manager import (
    scenarios,
    best_agents,
    meta_json,
    make_episode_without_decorate,
    make_episode,
    n_cores,
    retrieve_episode_from_disk,
    save_in_ram_cache,
    save_in_fs_cache,
    cache_dir,
    agents_dir,
    grid2viz_home_directory,
)
from grid2viz.src.utils.callbacks_helpers import toggle_modal_helper
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME


def register_callbacks_episodes(app):
    @app.callback(Output("cards_container", "children"), Input("url", "pathname"))
    def load_scenario_cards(url):
        """
        Create and display html cards with scenario's kpi for
        the 15 first scenarios using cache file.
        """
        cards_list = []
        cards_count = 0
        episode_graph_layout = {
            "autosize": True,
            "showlegend": False,
            "xaxis": {"showticklabels": False},
            "yaxis": {"showticklabels": False},
            "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
        }

        url_split = url.split("/")
        url_split = url_split[len(url_split) - 1]

        is_episode_page = url_split == "/" or url_split == "" or url_split == "episodes"
        start_time = time.time()
        if cards_count < 15 and is_episode_page:
            sorted_scenarios = list(sorted(scenarios))
            if not os.path.exists(cache_dir):
                print(
                    "Starting Multiprocessing for reading the best agent of each scenario"
                )
                pool = ProcessPool(n_cores)
                best_agents_data = list(
                    pool.imap(
                        make_episode_without_decorate,
                        [
                            best_agents[scenario]["agent"]
                            for scenario in sorted_scenarios
                        ],
                        sorted_scenarios,
                    )
                )
                pool.close()
                print("Multiprocessing done")
                for i, scenario in enumerate(sorted_scenarios):
                    best_agent_episode = best_agents_data[i]
                    episode_data = retrieve_episode_from_disk(
                        best_agent_episode.episode_name, best_agent_episode.agent
                    )
                    best_agent_episode.decorate_light_without_reboot(episode_data)

                    best_agent_episode.decorate_obs_act_spaces(os.path.join(agents_dir, best_agent_episode.agent))

                    #save_in_fs_cache(best_agent_episode.episode_name,
                    #    best_agent_episode.agent,
                    #    best_agent_episode)

                    save_in_ram_cache(
                        best_agent_episode.episode_name,
                        best_agent_episode.agent,
                        best_agent_episode,
                    )

            for i, scenario in enumerate(sorted_scenarios):
                best_agent_episode = make_episode(
                    best_agents[scenario]["agent"], scenario
                )
                prod_share = EpisodeTrace.get_prod_share_trace(best_agent_episode)
                consumption = best_agent_episode.profile_traces
                cards_list.append(
                    dbc.Col(
                        id=f"card_{scenario}",
                        lg=4,
                        width=12,
                        children=[
                            dbc.Card(
                                className="mb-3",
                                children=[
                                    dbc.CardBody(
                                        [
                                            html.H5(
                                                className="card-title",
                                                children="Scenario {0}".format(
                                                    scenario
                                                ),
                                            ),
                                            dbc.Row(
                                                children=[
                                                    dbc.Col(
                                                        className="mb-4",
                                                        children=[
                                                            html.P(
                                                                className="border-bottom h3 mb-0 text-right",
                                                                children=best_agents[
                                                                    scenario
                                                                ]["out_of"],
                                                            ),
                                                            html.P(
                                                                className="text-muted",
                                                                children="Agents on Scenario",
                                                            ),
                                                        ],
                                                    ),
                                                    dbc.Col(
                                                        className="mb-4",
                                                        children=[
                                                            html.P(
                                                                className="border-bottom h3 mb-0 text-right",
                                                                children="{}/{}".format(
                                                                    best_agents[
                                                                        scenario
                                                                    ]["value"],
                                                                    meta_json[scenario][
                                                                        "chronics_max_timestep"
                                                                    ],
                                                                ),
                                                            ),
                                                            html.P(
                                                                className="text-muted",
                                                                children="Agent's Survival",
                                                            ),
                                                        ],
                                                    ),
                                                    dbc.Col(
                                                        className="mb-4",
                                                        children=[
                                                            html.P(
                                                                className="border-bottom h3 mb-0 text-right",
                                                                children=f'{round(best_agents[scenario]["cum_reward"]):,}',
                                                            ),
                                                            html.P(
                                                                className="text-muted",
                                                                children="Cumulative Reward",
                                                            ),
                                                        ],
                                                    ),
                                                    dbc.Col(
                                                        className="mb-4",
                                                        children=[
                                                            html.P(
                                                                className="border-bottom h3 mb-0 text-right",
                                                                children="{} min".format(
                                                                    round(
                                                                        best_agent_episode.total_maintenance_duration
                                                                    )
                                                                ),
                                                            ),
                                                            html.P(
                                                                className="text-muted",
                                                                children="Total Maintenance Duration",
                                                            ),
                                                        ],
                                                    ),
                                                ]
                                            ),
                                            dbc.Row(
                                                className="align-items-center",
                                                children=[
                                                    dbc.Col(
                                                        lg=4,
                                                        width=12,
                                                        children=[
                                                            html.H5(
                                                                "Production Share",
                                                                className="text-center",
                                                            ),
                                                            dcc.Graph(
                                                                style={
                                                                    "height": "150px"
                                                                },
                                                                figure=go.Figure(
                                                                    layout=episode_graph_layout,
                                                                    data=prod_share,
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                    dbc.Col(
                                                        lg=8,
                                                        width=12,
                                                        children=[
                                                            html.H5(
                                                                "Consumption Profile",
                                                                className="text-center",
                                                            ),
                                                            dcc.Graph(
                                                                style={
                                                                    "height": "150px"
                                                                },
                                                                figure=go.Figure(
                                                                    layout=episode_graph_layout,
                                                                    data=consumption,
                                                                ),
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        dbc.Button(
                                            "Open",
                                            id=scenario,
                                            key=scenario,
                                            className="btn-block",
                                            style={"background-color": "#2196F3"},
                                        )
                                    ),
                                ],
                            )
                        ],
                    )
                )
                cards_count += 1
        print(
            "Initial loading time for the best agent of all scenarios = {:.1f} seconds".format(
                time.time() - start_time
            )
        )
        return cards_list

    @app.callback(
        [Output("scenario", "data"), Output("url", "pathname")],
        [Input(scenario, "n_clicks") for scenario in scenarios],
        [State(scenario, "key") for scenario in scenarios],
    )
    def open_scenario(*input_state):
        """
        Open scenario into the overview layout when button
        corresponding button is clicked.

        Use callback context to get triggered input then parse it to get triggered input id
        then get the state key value from context with is the dict key (input_id + '.key').

        .. note:: you may need to see https://dash.plot.ly/faqs to get how I determine which Input has changed
        """

        ctx = callback_context

        # No clicks
        if not ctx.triggered:
            raise PreventUpdate
        # No clicks again
        # https://github.com/plotly/dash/issues/684
        if ctx.triggered[0]["value"] is None:
            raise PreventUpdate

        input_id = ctx.triggered[0]["prop_id"].split(".")[0]
        input_key = ctx.states[input_id + ".key"]
        scenario = input_key

        return scenario, "/overview"

    @app.callback(
        [
            Output("modal_episodes", "is_open"),
            Output("dont_show_again_div_episodes", "className"),
        ],
        [Input("close_episodes", "n_clicks"), Input("page_help", "n_clicks")],
        [
            State("modal_episodes", "is_open"),
            State("dont_show_again_episodes", "checked"),
        ],
    )
    def toggle_modal(close_n_clicks, open_n_clicks, is_open, dont_show_again):
        dsa_filepath = Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("episodes")
        return toggle_modal_helper(
            close_n_clicks,
            open_n_clicks,
            is_open,
            dont_show_again,
            dsa_filepath,
            "page_help",
        )

    @app.callback(
        Output("collapse", "is_open"),
        [Input("collapse-button", "n_clicks")],
        [State("collapse", "is_open")],
    )
    def toggle_collapse(n, is_open):
        if n:
            return not is_open
        return is_open

    @app.callback(Output("modal_image_episodes", "src"), [Input("url", "pathname")])
    def show_image(pathname):
        return app.get_asset_url("screenshots/scenario_selection.png")

    @app.callback(
        Output("scenario_filter_div", "className"), [Input("collapse", "is_open")]
    )
    def toggle_scenario_filter(is_open):
        if is_open:
            return ""
        else:
            return "hidden"

    def filter_scenarios(selected_scenarios, scenario):
        if selected_scenarios is None:
            raise PreventUpdate
        if scenario in selected_scenarios:
            return ""
        else:
            return "hidden"

    for scenario in scenarios:
        app.callback(
            Output(f"card_{scenario}", "className"),
            [Input("scenarios_filter", "value")],
        )(partial(filter_scenarios, scenario=scenario))
