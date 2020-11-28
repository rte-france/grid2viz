import json
from pathlib import Path

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from grid2op.Agent import DoNothingAgent
from grid2op.Episode import EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters

from grid2viz.src.manager import make_episode, make_network


def register_callbacks_simulation(app):
    @app.callback(
        [
            Output("action_dictionary", "children"),
            Output("network_graph_choose", "figure"),
        ],
        [Input("simulate_action", "n_clicks")],
        [
            State("textarea", "value"),
            State("agent_study", "data"),
            State("scenario", "data"),
        ],
    )
    def update_action(n_clicks, action_dict, agent, scenario):
        episode = make_episode(agent, scenario)
        if action_dict is None:
            raise PreventUpdate
        action_dict = json.loads(action_dict.replace("(", "[").replace(")", "]"))

        # Temporary implementation for testing purposes
        p = Parameters()
        p.NO_OVERFLOW_DISCONNECTION = False
        env = make(
            r"D:\Projects\RTE-Grid2Viz\Grid2Op\grid2op\data\rte_case14_realistic",
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
        agent_path = r"D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/do-nothing-baseline"
        episode_reboot.load(
            env.backend,
            data=episode,
            agent_path=agent_path,
            name=episode.episode_name,
            env_kwargs=params_for_reboot,
        )
        current_time_step = 0
        obs, reward, *_ = episode_reboot.go_to(1)
        agent = DoNothingAgent(action_space=episode_reboot.env.action_space)
        act = agent.act(obs, reward)
        act = act.update(action_dict)
        obs, *_ = obs.simulate(action=act, time_step=0)
        network_graph = make_network(episode).plot_obs(observation=obs)
        return json.dumps(action_dict, indent=1), network_graph
