import os
from contextlib import redirect_stdout

import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
from alphaDeesp.core.grid2op.Grid2opSimulation import (
    Grid2opSimulation,
)
from alphaDeesp.expert_operator import expert_operator
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash_table import DataTable
from grid2op.Action import PlayableAction
from grid2op.Episode import EpisodeReboot
from grid2op.PlotGrid import PlotPlotly

from grid2viz.src.manager import make_episode, agents_dir
from grid2viz.src.simulation.reboot import env, params_for_reboot, BACKEND
from grid2viz.src.simulation.simulation_assist import BaseAssistant
from grid2viz.src.kpi.EpisodeAnalytics import compute_losses

try:
    from lightsim2grid.LightSimBackend import LightSimBackend

    BACKEND = LightSimBackend
except ModuleNotFoundError:
    from grid2op.Backend import PandaPowerBackend

    BACKEND = PandaPowerBackend

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
        self.obs_reboot = None
        self.episode_reboot=None

    def layout(self, episode):
        return html.Div(
            [
                dcc.Store(id="assistant_store"),
                dcc.Store(id="assistant_actions"),
                dcc.Store(
                    id="assistant-size", data=dict(assist="col-3", graph="col-9")
                ),
                html.P("Choose a line to study:", className="my-2"),
                dac.Select(
                    id="select_lines_to_cut",
                    options=[
                        {"label": line_name, "value": line_name}
                        for line_name in episode.line_names
                    ],
                    mode="default",
                    value=episode.line_names[0],
                ),
                html.P("Flow ratio (in %) to get below"),
                dbc.Input(
                    type="number",
                    min=0,
                    max=100,
                    step=1,
                    id="input_flow_ratio",
                    value=100,
                ),
                # dbc.Checklist(
                #     options=[
                #         {"label": "Generate snapshots", "value": 1},
                #     ],
                #     value=[],
                #     id="generate_snapshot_id",
                #     inline=True,
                # ),
                html.P("Number of simulations to run:", className="my-2"),
                dbc.Input(
                    type="number",
                    min=0,
                    max=50,
                    step=1,
                    id="input_nb_simulations",
                    value=15,
                ),
                dbc.Button(
                    id="assist-evaluate",
                    children=["Evaluate with the Expert system"],
                    color="danger",
                    className="m-3",
                ),
                dbc.Button(
                    id="assist-reset",
                    children=["Reset"],
                    color="secondary",
                    className="m-3",
                ),
                html.Div(id="expert-results"),
                html.P(
                    id="assist-action-info",
                    className="more-info-table",
                    children="Select an action in the table above.",
                ),
                dcc.Link(
                    "See the ExpertOP4Grid documentation for more information",
                    href="https://expertop4grid.readthedocs.io/en/latest/DESCRIPTION.html#didactic-example",
                ),
            ]
        )

    def register_callbacks(self, app):
        @app.callback(
            [
                Output("expert-results", "children"),
                Output("assistant_actions", "data"),
                Output("assistant-size", "data"),
            ],
            [Input("assist-evaluate", "n_clicks"), Input("assist-reset", "n_clicks")],
            [
                State("scenario", "data"),
                State("agent_study", "data"),
                State("user_timestep_store", "data"),
                State("input_nb_simulations", "value"),
                State("input_flow_ratio", "value"),
                State("select_lines_to_cut", "value"),
            ],
        )
        def evaluate_expert_system(
            evaluate_n_clicks,
            reset_n_clicks,
            scenario,
            agent,
            ts,
            nb_simulations,
            flow_ratio,
            line_to_study,
        ):
            if evaluate_n_clicks is None:
                raise PreventUpdate

            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate
            else:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "assist-evaluate":
                assistant_size = dict(assist="col-12", graph="hidden")
            else:
                assistant_size = dict(assist="col-3", graph="col-9")
                return "", [], assistant_size
            thermal_limit = env.get_thermal_limit()
            # with redirect_stdout(None):
            if nb_simulations is not None:
                expert_config["totalnumberofsimulatedtopos"] = nb_simulations
            episode = make_episode(episode_name=scenario, agent=agent,with_reboot=True)
            if flow_ratio is not None and line_to_study is not None:
                new_thermal_limit = thermal_limit.copy()
                line_id = np.where(episode.line_names == line_to_study)[0][0]
                new_thermal_limit[line_id] = (
                    flow_ratio / 100.0 * new_thermal_limit[line_id]
                )

            episode_reboot = EpisodeReboot.EpisodeReboot()

            episode_reboot.load(
                #env.backend,
                BACKEND(),
                data=episode,
                agent_path=os.path.join(agents_dir, episode.agent),
                name=episode.episode_name,
                env_kwargs=params_for_reboot,
            )
            if(ts<=0):
                ts=1 #cannot reboot for ts<=0

            episode_reboot.env.set_thermal_limit(new_thermal_limit)
            obs, reward, *_ = episode_reboot.go_to(int(ts))
            if not np.all(
                np.round(episode.observations[int(ts)].a_or, 2) == np.round(obs.a_or, 2)
            ):
                return (
                    html.Div(
                        children=f"Issue - Unable to reboot episode at time step {ts} for agent {episode.agent}",
                        className="more-info-table",
                    ),
                    [],
                    assistant_size,
                )
            # fictively changing obs.rho and thermal limits to be used by the expert system
            # also making sure that obs thermal_limits are initialized, not to dafault large values as given by reboot
            obs.rho #= obs.rho * obs._obs_env.get_thermal_limit() / new_thermal_limit
            #obs._obs_env.set_thermal_limit(new_thermal_limit)

            if line_to_study is not None:
                line_id = np.where(episode.line_names == line_to_study)[0][0]
                ltc = [line_id]
            else:
                ltc = [get_ranked_overloads(env.observation_space, obs)[0]]
            with redirect_stdout(None):
                simulator = Grid2opSimulation(
                    obs,
                    env.action_space,env.observation_space,
                    param_options=expert_config,
                    debug=False,
                    ltc=ltc,
                    reward_type=reward_type,
                )

                ranked_combinations, expert_system_results, actions = expert_operator(
                    simulator, plot=False, debug=False
                )
            # reinitialize proper thermal limits
            episode_reboot.env.set_thermal_limit(env.get_thermal_limit())
            self.obs_reboot, reward, *_ = episode_reboot.go_to(int(ts))
            self.episode_reboot = episode_reboot #important to not close the associated env that will be necessary later for simulate

            expert_system_results = expert_system_results.sort_values(
                ["Topology simulated score", "Efficacity"], ascending=False
            )
            actions = [actions[i] for i in expert_system_results.index]

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
                [action.to_vect() for action in actions],
                assistant_size,
            )

        @app.callback(
            [
                Output("assistant_store", "data"),
                Output("assist-action-info", "children"),
            ],
            [Input("table", "selected_rows"), Input("assist-reset", "n_clicks")],
            [State("assistant_actions", "data")],
        )
        def select_action(selected_rows, n_clicks, actions):
            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate
            else:
                component_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if component_id == "assist-reset":
                return [], ""
            if selected_rows is None:
                raise PreventUpdate
            selected_row = selected_rows[0]
            action = actions[selected_row]
            act = env.action_space.from_vect(np.array(action))
            return action, str(act)

    def store_to_graph(self, store_data, episode, ts):
        if ts==0:
            ts=1
        episode_reboot = EpisodeReboot.EpisodeReboot()
        episode_reboot.load(
           BACKEND(),
           data=episode,
           agent_path=os.path.join(agents_dir, episode.agent),
           name=episode.episode_name,
           env_kwargs=params_for_reboot,
        )
        episode_reboot.env.set_thermal_limit(env.get_thermal_limit())

        obs_reboot, reward, *_ = episode_reboot.go_to(ts)
        act = env.action_space.from_vect(np.array(store_data))
        #if self.obs_reboot is not None:
        if obs_reboot is not None:
            #obs, *_ = self.obs_reboot.simulate(action=act, time_step=0)
            obs, *_ = obs_reboot.simulate(action=act, time_step=0)
            # make sure rho is properly calibrated. Problem could be that obs_reboot thermal limits are not properly initialized
            obs.rho = (
                obs.rho
                * self.obs_reboot._obs_env.get_thermal_limit()
                / env.get_thermal_limit()
            )
            try:
                network_graph_factory = PlotPlotly(
                    grid_layout=episode.observation_space.grid_layout,
                    observation_space=episode.observation_space,
                    responsive=True,
                )
                new_network_graph = network_graph_factory.plot_obs(observation=obs)
            except ValueError:
                import traceback

                new_network_graph = traceback.format_exc()

            return new_network_graph

    def store_to_kpis(self, store_data, episode, ts):
        act = env.action_space.from_vect(np.array(store_data))
        if self.obs_reboot is not None:
            obs, reward, *_ = self.obs_reboot.simulate(action=act, time_step=0)
            # make sure rho is properly calibrated. Problem could be that obs_reboot thermal limits are not properly initialized
            obs.rho = (
                obs.rho
                * self.obs_reboot._obs_env.get_thermal_limit()
                / env.get_thermal_limit()
            )
        else:
            raise RuntimeError(
                f"Assist.store_to_kpis cannot be called before first rebooting the Episode"
            )
        rho_max = f"{obs.rho.max() * 100:.0f}%"
        nb_overflows = f"{(obs.rho > 1).sum():,.0f}"
        losses = f"{compute_losses(obs)*100:.2f}%"
        return reward, rho_max, nb_overflows, losses
