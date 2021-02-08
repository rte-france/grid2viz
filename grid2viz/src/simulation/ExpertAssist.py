import os

import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dill
import numpy as np
from alphaDeesp.core.grid2op.Grid2opSimulation import (
    Grid2opSimulation,
)
from alphaDeesp.expert_operator import expert_operator
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable
from grid2op.Action import PlayableAction
from grid2op.Episode import EpisodeData, EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters
from grid2op.PlotGrid import PlotPlotly

from contextlib import redirect_stdout

from grid2viz.src.simulation.simulation_assist import BaseAssistant

scenario = "000"
agent = "do-nothing-baseline"
agent_dir = "D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/" + agent
path = r"D:\Projects\RTE-Grid2Viz\grid2viz\grid2viz\data\agents\_cache\000\do-nothing-baseline.dill"
agent_path = (
    r"D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/do-nothing-baseline"
)
env_path = r"D:\Projects\RTE-Grid2Viz\Grid2Op\grid2op\data\rte_case14_realistic"
with open(path, "rb") as f:
    episode = dill.load(f)
episode_data = EpisodeData.from_disk(agent_dir, scenario)
episode.decorate(episode_data)

network_graph_factory = PlotPlotly(
    grid_layout=episode.observation_space.grid_layout,
    observation_space=episode.observation_space,
    responsive=True,
)

expert_config = {
    "totalnumberofsimulatedtopos": 25,
    "numberofsimulatedtopospernode": 5,
    "maxUnusedLines": 2,
    "ratioToReconsiderFlowDirection": 0.75,
    "ratioToKeepLoop": 0.25,
    "ThersholdMinPowerOfLoop": 0.1,
    "ThresholdReportOfLine": 0.2,
}

reward_type = "MinMargin_reward"

p = Parameters()
p.NO_OVERFLOW_DISCONNECTION = False
env = make(
    env_path,
    test=True,
    param=p,
)
env.seed(0)

params_for_runner = env.get_params_for_runner()
params_to_fetch = ["init_grid_path"]
params_for_reboot = {
    key: value for key, value in params_for_runner.items() if key in params_to_fetch
}
params_for_reboot["parameters"] = p

episode_reboot = EpisodeReboot.EpisodeReboot()

episode_reboot.load(
    env.backend,
    data=episode,
    agent_path=agent_path,
    name=episode.episode_name,
    env_kwargs=params_for_reboot,
)

t = 1

obs, reward, *_ = episode_reboot.go_to(t)


def get_ranked_overloads(observation_space, observation):
    timestepsOverflowAllowed = (
        3  # observation_space.parameters.NB_TIMESTEP_OVERFLOW_ALLOWED
    )

    sort_rho = -np.sort(
        -observation.rho
    )  # sort in descending order for positive values
    sort_indices = np.argsort(-observation.rho)
    ltc_list = [sort_indices[i] for i in range(len(sort_rho)) if sort_rho[i] >= 1]

    # now reprioritize ltc if critical or not
    ltc_critical = [
        l
        for l in ltc_list
        if (observation.timestep_overflow[l] == timestepsOverflowAllowed)
    ]
    ltc_not_critical = [
        l
        for l in ltc_list
        if (observation.timestep_overflow[l] != timestepsOverflowAllowed)
    ]

    ltc_list = ltc_critical + ltc_not_critical
    if len(ltc_list) == 0:
        ltc_list = [sort_indices[0]]
    return ltc_list


class Assist(BaseAssistant):
    def __init__(self):
        super().__init__()

    def layout(self, episode):
        return html.Div(
            [
                dcc.Store(id="assistant_store"),
                dcc.Store(id="assistant_actions"),
                html.P("Choose a line to cut:", className="my-2"),
                dac.Select(
                    id="select_lines_to_cut",
                    options=[
                        {"label": line_name, "value": line_name}
                        for line_name in episode.line_names
                    ],
                    mode="default",
                    value=episode.line_names[0],
                ),
                dbc.Checklist(
                    options=[
                        {"label": "Generate snapshots", "value": 1},
                    ],
                    value=[],
                    id="generate_snapshot_id",
                    inline=True,
                ),
                html.P("Chose a chronics scenario:", className="my-2"),
                dbc.Input(
                    type="number", min=0, max=10, step=1, id="input_chronics_scenario"
                ),
                dbc.Button(
                    id="assist-button", children=["Evaluate with the Expert system"]
                ),
                html.Div(id="expert-results"),
                html.P(
                    id="assist-action-info",
                    className="more-info-table",
                    children="Select an action in the table above.",
                ),
            ]
        )

    def register_callbacks(self, app):
        @app.callback(
            [Output("expert-results", "children"), Output("assistant_actions", "data")],
            [Input("assist-button", "n_clicks")],
        )
        def evaluate_expert_system(n_clicks):
            if n_clicks is None:
                raise PreventUpdate
            with redirect_stdout(None):
                simulator = Grid2opSimulation(
                    obs,
                    env.action_space,
                    env.observation_space,
                    param_options=expert_config,
                    debug=False,
                    ltc=[get_ranked_overloads(env.observation_space, obs)[0]],
                    reward_type=reward_type,
                )
                ranked_combinations, expert_system_results, actions = expert_operator(
                    simulator, plot=False, debug=False
                )
            return (
                DataTable(
                    id="table",
                    columns=[
                        {"name": i, "id": i} for i in expert_system_results.columns
                    ],
                    data=expert_system_results.to_dict("records"),
                    style_table={"overflowX": "auto"},
                    row_selectable="single",
                    style_cell={
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "maxWidth": 0,
                    },
                    tooltip_data=[
                        {
                            column: {"value": str(value), "type": "markdown"}
                            for column, value in row.items()
                        }
                        for row in expert_system_results.to_dict("rows")
                    ],
                ),
                [action.as_dict() for action in actions],
            )

        @app.callback(
            [
                Output("assistant_store", "data"),
                Output("assist-action-info", "children"),
            ],
            [Input("table", "selected_rows")],
            [State("assistant_actions", "data")],
        )
        def select_action(selected_rows, actions):
            if selected_rows is None:
                raise PreventUpdate
            selected_row = selected_rows[0]
            action = actions[selected_row]
            act = PlayableAction()
            act.update(action)
            return action, str(act)

    def store_to_graph(self, store_data):
        p = Parameters()
        p.NO_OVERFLOW_DISCONNECTION = False
        env = make(
            env_path,
            test=True,
            param=p,
        )
        env.seed(0)

        params_for_runner = env.get_params_for_runner()
        params_to_fetch = ["init_grid_path"]
        params_for_reboot = {
            key: value
            for key, value in params_for_runner.items()
            if key in params_to_fetch
        }
        params_for_reboot["parameters"] = p

        episode_reboot = EpisodeReboot.EpisodeReboot()
        episode_reboot.load(
            env.backend,
            data=episode,
            agent_path=agent_path,
            name=episode.episode_name,
            env_kwargs=params_for_reboot,
        )
        obs, reward, *_ = episode_reboot.go_to(t)
        act = PlayableAction()
        act.update(store_data)
        obs, *_ = obs.simulate(action=act, time_step=0)
        try:
            new_network_graph = network_graph_factory.plot_obs(observation=obs)
        except ValueError:
            import traceback

            new_network_graph = traceback.format_exc()

        return new_network_graph
