import json
import json
import os

import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from grid2op.Action import PlayableAction
from grid2op.Episode import EpisodeReboot

from grid2viz.src.manager import make_episode, make_network_agent_study
from grid2viz.src.manager import make_network, agents_dir
from grid2viz.src.simulation.reboot import env, params_for_reboot, BACKEND
from grid2viz.src.simulation.simulation_lyt import choose_tab_content
from grid2viz.src.utils.serialization import NoIndent, MyEncoder
from grid2viz.src.simulation.simulation_utils import action_dict_from_choose_tab
from grid2viz.src.kpi.EpisodeAnalytics import compute_losses


def register_callbacks_simulation(app, assistant):
    @app.callback(
        Output("tabs-choose-assist-method-content", "children"),
        [Input("tabs-choose-assist-method", "active_tab")],
        [
            State("scenario", "data"),
            State("agent_study", "data"),
        ],
    )
    def simulation_method_tab_content(active_tab, scenario, study_agent):
        episode = make_episode(study_agent, scenario)
        if active_tab is None:
            raise PreventUpdate
        if active_tab == "tab-choose-method":
            return choose_tab_content(episode)
        elif active_tab == "tab-assist-method":
            return assistant.register_layout(
                episode, layout_to_ckeck_against=choose_tab_content(episode)
            )

    @app.callback(
        [
            Output("div-choose-assist", "class"),
            Output("div-network-graph-choose-assist", "class"),
        ],
        [
            Input("tabs-choose-assist-method", "active_tab"),
            Input("simulation-assistant-size", "data"),
        ],
    )
    def simulation_method_tab_content(active_tab, data):
        if active_tab is None:
            raise PreventUpdate
        if active_tab == "tab-choose-method":
            return "col-3", "col-9"
        elif active_tab == "tab-assist-method":
            if data is None:
                assist_size = "col-3"
                graph_size = "col-9"
            else:
                assist_size = data["assist"]
                graph_size = data["graph"]
            return assist_size, graph_size

    @app.callback(
        Output("network_graph_t", "data"),
        [Input("agent_study", "data"), Input("user_timestep_store", "data")],
        [State("scenario", "data")],
    )
    def update_network_graph_t(study_agent, ts, scenario):
        if study_agent is None or scenario is None or ts is None:
            raise PreventUpdate
        episode = make_episode(study_agent, scenario)
        return make_network_agent_study(episode, timestep=int(ts), responsive=True)

    @app.callback(
        [
            Output("actions", "data"),
            Output("action_info", "children"),
            Output("graph_div", "children"),
            Output("textarea", "value"),
            Output("network_graph_new", "data"),
        ],
        [
            Input("add_action", "n_clicks"),
            Input("reset_action", "n_clicks"),
            Input("network_graph_t", "data"),
        ],
        [
            State("actions", "data"),
            State("textarea", "value"),
            State("tab_method", "active_tab"),
            State("tab_object", "active_tab"),
            State("select_lines_simulation", "value"),
            State("select_loads_simulation", "value"),
            State("select_gens_simulation", "value"),
            State("radio_topology_type_lines", "value"),
            State("radio_disc_rec_lines", "value"),
            State("radio_target_lines", "value"),
            State("radio_bus_lines", "value"),
            State("radio_ex_or_lines", "value"),
            State("radio_topology_type_loads", "value"),
            State("radio_bus_loads", "value"),
            State("radio_action_type_gens", "value"),
            State("radio_topology_type_gens", "value"),
            State("radio_bus_gens", "value"),
            State("input_redispatch", "value"),
            State("network_graph_new", "data"),
            State("scenario", "data"),
            State("agent_study", "data"),
            State("user_timestamps", "value"),
            State("user_timestep_store", "data"),
        ],
    )
    def update_action(
        add_n_clicks,
        reset_n_clicks,
        network_graph_t,
        actions,
        action_dict,
        method_tab,
        objet_tab,
        selected_line,
        selected_load,
        selected_gen,
        topology_type_lines,
        disc_rec_lines,
        target_lines,
        bus_lines,
        ex_or_lines,
        topology_type_loads,
        bus_loads,
        action_type_gens,
        topology_type_gens,
        bus_gens,
        redisp_volume,
        network_graph_new,
        scenario,
        study_agent,
        timestamp,
        timestep,
    ):
        ctx = callback_context

        if timestep<=0:
            timestep=1

        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "reset_action" or button_id == "network_graph_t":
            graph_div = dcc.Graph(figure=network_graph_t)
            return (
                None,
                "Compose some actions to study",
                graph_div,
                None,
                network_graph_t,
            )

        if add_n_clicks is None:
            raise PreventUpdate
        episode = make_episode(study_agent, scenario,with_reboot=True)
        if method_tab == "tab_method_dropdowns":
            # Dropdown
            if objet_tab == "tab_object_lines":
                # Lines
                params_dict = dict(
                    ex_or_lines=ex_or_lines,
                    target_lines=target_lines,
                    disc_rec_lines=disc_rec_lines,
                )
                action_dict = action_dict_from_choose_tab(
                    episode,
                    kind="Lines",
                    selected_object=selected_line,
                    bus=bus_lines,
                    topology_type=topology_type_lines,
                    params_dict=params_dict,
                )

            elif objet_tab == "tab_object_loads":
                # Loads
                action_dict = action_dict_from_choose_tab(
                    episode,
                    kind="Loads",
                    selected_object=selected_load,
                    bus=bus_loads,
                    topology_type=topology_type_loads,
                )
            else:
                # Gens: tab_object_gens
                params_dict = dict(
                    action_type_gens=action_type_gens,
                    redisp_volume=redisp_volume,
                )
                action_dict = action_dict_from_choose_tab(
                    episode,
                    kind="Gens",
                    selected_object=selected_gen,
                    bus=bus_gens,
                    topology_type=topology_type_gens,
                    params_dict=params_dict,
                )
            if actions is None:
                actions = [action_dict]
            else:
                actions.append(action_dict)
        else:
            # Dict: tab_method_dict
            if action_dict is None:
                raise PreventUpdate
            try:
                action_dict = json.loads(
                    action_dict.replace("(", "[").replace(")", "]")
                )
            except json.decoder.JSONDecodeError as ex:
                import traceback

                graph_div_child = html.Div(
                    children=traceback.format_exc(), className="more-info-table"
                )
                return actions, "", graph_div_child, action_dict, network_graph_t
            if "action_list" in action_dict:
                actions_for_textarea = action_dict["action_list"]
            else:
                actions_for_textarea = [action_dict]
            if actions is None:
                actions = actions_for_textarea
            else:
                actions.extend(actions_for_textarea)

        episode_reboot = EpisodeReboot.EpisodeReboot()
        episode_reboot.load(
            BACKEND(),
            data=episode,
            agent_path=os.path.join(agents_dir, study_agent),
            name=episode.episode_name,
            env_kwargs=params_for_reboot,
        )
        episode_reboot.env.set_thermal_limit(env.get_thermal_limit())
        obs, reward, *_ = episode_reboot.go_to(int(timestep))
        #obs._obs_env.set_thermal_limit(env.get_thermal_limit())
        act = env.action_space()

        if not np.all(
            np.round(episode.observations[int(timestep)].a_or, 2)
            == np.round(obs.a_or, 2)
        ):
            return (
                actions,
                "",
                html.Div(
                    children=f"Issue - Unable to reboot episode at time step {timestep} for agent {episode.agent}",
                    className="more-info-table",
                ),
                "",
                network_graph_t,
            )

        for action in actions:
            act.update(action)
        obs, *_ = obs.simulate(action=act, time_step=0)

        try:
            graph_div_child = dcc.Graph(figure=network_graph_t)
            new_network_graph = make_network(episode).plot_obs(observation=obs)
        except ValueError:
            import traceback

            graph_div_child = html.Div(
                children=traceback.format_exc(), className="more-info-table"
            )
            new_network_graph = network_graph_t

        try:
            json.dumps(actions)
        except Exception as ex:
            print("actions")
            print(actions)
        if method_tab == "tab_method_dropdowns":
            return (
                actions,
                str(act),
                graph_div_child,
                json.dumps(
                    (dict(action_list=[NoIndent(action) for action in actions])),
                    indent=2,
                    sort_keys=True,
                    cls=MyEncoder,
                ),
                new_network_graph,
            )
        else:
            actions_for_textarea = dict(
                action_list=[
                    *[NoIndent(action) for action in actions[:-1]],
                    actions[-1],
                ]
            )

            return (
                actions,
                str(act),
                graph_div_child,
                json.dumps(
                    (dict(action_list=[NoIndent(action) for action in actions])),
                    indent=2,
                    sort_keys=True,
                    cls=MyEncoder,
                ),
                new_network_graph,
            )

    @app.callback(
        [
            Output("radio_disc_rec_lines", "className"),
            Output("radio_target_lines", "className"),
            Output("radio_bus_lines", "className"),
            Output("radio_ex_or_lines", "className"),
        ],
        [
            Input("radio_topology_type_lines", "value"),
            Input("radio_target_lines", "value"),
        ],
    )
    def toggle_radio_lines(radio_topology_type_lines, radio_target_lines):
        if radio_topology_type_lines != "Set":
            return "hidden", "mt-1", "hidden", "hidden"
        else:
            if radio_target_lines != "Status":
                return "hidden", "mt-1", "mt-1", "mt-1"
            else:
                return "mt-1", "mt-1", "hidden", "hidden"

    @app.callback(
        Output("radio_bus_loads", "className"),
        [Input("radio_topology_type_loads", "value")],
    )
    def toggle_radio_loads(radio_topology_type_loads):
        if radio_topology_type_loads != "Set":
            return "hidden"
        else:
            return "mt-1"

    @app.callback(
        [
            Output("input_redispatch", "className"),
            Output("radio_topology_type_gens", "className"),
            Output("radio_bus_gens", "className"),
        ],
        [
            Input("radio_action_type_gens", "value"),
            Input("radio_topology_type_gens", "value"),
        ],
    )
    def toggle_radio_gens(radio_action_type_gens, radio_topology_type_gens):
        if radio_action_type_gens == "Redispatch":
            return "mt-1", "hidden", "hidden"
        else:
            # Topology action
            if radio_topology_type_gens == "Set":
                return "hidden", "mt-1", "mt-1"
            else:
                # Change
                return "hidden", "mt-1", "hidden"

    @app.callback(
        Output("card_body_network", "children"),
        [Input("simulate_action", "n_clicks")],
        [
            State("actions", "data"),
            State("network_graph_new", "data"),
            State("tabs-choose-assist-method", "active_tab"),
            State("simulation-assistant-store", "data"),
            State("scenario", "data"),
            State("agent_study", "data"),
            State("user_timestep_store", "data"),
            State("network_graph_t", "data"),
        ],
    )
    def simulate(
        simulate_n_clicks,
        actions,
        network_graph_new,
        active_tab_choose_assist,
        simulation_assistant_store,
        scenario,
        agent,
        ts,
        network_graph_t,
    ):
        if simulate_n_clicks is None:
            return
        if actions is None and simulation_assistant_store is None:
            return "No action performed"
        if active_tab_choose_assist == "tab-assist-method":
            episode = make_episode(agent, scenario)
            return dcc.Graph(
                figure=go.Figure(
                    assistant.store_to_graph(
                        simulation_assistant_store, episode, int(ts)
                    )
                )
            )
        else:
            if actions:
                return dcc.Graph(figure=network_graph_new)
            else:
                return dcc.Graph(figure=network_graph_t)

    @app.callback(
        [
            Output("agent_reward", "children"),
            Output("agent_rho", "children"),
            Output("agent_overflows", "children"),
            Output("agent_losses", "children"),
        ],
        [Input("network_graph_t", "data"), Input("user_timestep_store", "data")],
        [
            State("agent_study", "data"),
            State("scenario", "data"),
        ],
    )
    def update_kpis(
        network_graph_t,
        ts,
        study_agent,
        scenario,
    ):
        episode = make_episode(study_agent, scenario)
        reward = f"{episode.rewards[int(ts)]:,.0f}"
        rho_max = (
            f"{episode.rho.loc[episode.rho.time == int(ts), 'value'].max() * 100:.0f}%"
        )
        nb_overflows = f"{episode.total_overflow_ts['value'][int(ts)]:,.0f}"
        losses = f"{compute_losses(episode.observations[int(ts)])*100:.2f}%"
        return reward, rho_max, nb_overflows, losses

    @app.callback(
        [
            Output("new_action_reward", "children"),
            Output("new_action_rho", "children"),
            Output("new_action_overflows", "children"),
            Output("new_action_losses", "children"),
        ],
        [Input("simulate_action", "n_clicks")],
        [
            State("tabs-choose-assist-method", "active_tab"),
            State("scenario", "data"),
            State("agent_study", "data"),
            State("user_timestep_store", "data"),
            State("simulation-assistant-store", "data"),
            State("actions", "data"),
        ],
    )
    def update_kpis_new_action(
        simulate_n_clicks,
        active_tab_choose_assist,
        scenario,
        study_agent,
        ts,
        simulation_assistant_store,
        actions,
    ):
        if simulate_n_clicks is None:
            raise PreventUpdate
        episode = make_episode(study_agent, scenario)
        if active_tab_choose_assist == "tab-choose-method":
            episode_reboot = EpisodeReboot.EpisodeReboot()
            episode_reboot.load(
                BACKEND(),
                data=episode,
                agent_path=os.path.join(agents_dir, study_agent),
                name=episode.episode_name,
                env_kwargs=params_for_reboot,
            )
            reward = f"0"
            rho_max = f"0"
            nb_overflows = f"0"
            losses = f"0"

            if(ts<=0):
                ts=1 #cannot reboot for ts<=0

            episode_reboot.env.set_thermal_limit(env.get_thermal_limit())
            obs_reboot, reward, *_ = episode_reboot.go_to(int(ts))
            if not np.all(
                np.round(episode.observations[int(ts)].a_or, 2) == np.round(obs_reboot.a_or, 2)
            ):
                return reward, rho_max, nb_overflows, losses
            act = env.action_space()
            if actions:
                for action in actions:
                    act.update(action)
                obs, reward, *_ = obs_reboot.simulate(action=act, time_step=0)
                rho_max = f"{obs.rho.max() * 100:.0f}%"
                nb_overflows = f"{(obs.rho > 1).sum():,.0f}"
                losses = f"{compute_losses(obs)*100:.2f}%"
            return reward, rho_max, nb_overflows, losses
        else:
            return assistant.store_to_kpis(simulation_assistant_store, episode, int(ts))

    @app.callback(
        [
            Output("simulation-assistant-store", "data"),
            Output("simulation-assistant-size", "data"),
        ],
        [Input("assistant_store", "data"), Input("assistant-size", "data")],
    )
    def transfer_assistant_store(store, size):
        """Necessary so that the store can be reach even when the assistant_store is
        not part of the view (e.g. when in choose mode)"""
        return store, size
