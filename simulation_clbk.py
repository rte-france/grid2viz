import json

import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly.graph_objects as go
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from grid2op.Action import PlayableAction
from grid2op.Episode import EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters

from grid2viz.src.utils.serialization import NoIndent, MyEncoder
from manager_simulation import make_episode, make_network, assistant, agents_dir
from simulation_lyt import choose_tab_content


def register_callbacks_simulation(app):
    @app.callback(
        [
            Output("tabs-choose-assist-method-content", "children"),
            Output("div-choose-assist", "class"),
            Output("div-network-graph-choose-assist", "class"),
        ],
        [Input("tabs-choose-assist-method", "active_tab")],
        [State("scenario", "data"), State("agent_study", "data")],
    )
    def simulation_method_tab_content(active_tab, scenario, study_agent):
        episode = make_episode(study_agent, scenario)
        if active_tab is None:
            raise PreventUpdate
        if active_tab == "tab-choose-method":
            return choose_tab_content(episode), "col-3", "col-9"
        elif active_tab == "tab-assist-method":
            return (
                assistant.register_layout(
                    episode, layout_to_ckeck_against=choose_tab_content(episode)
                ),
                "col-12",
                "hidden",
            )

    @app.callback(
        [
            Output("actions", "data"),
            Output("action_info", "children"),
            Output("graph_div", "children"),
            Output("textarea", "value"),
            Output("network_graph_new", "data"),
        ],
        [Input("add_action", "n_clicks"), Input("reset_action", "n_clicks")],
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
            State("network_graph_t", "data"),
            State("network_graph_t+1", "data"),
            State("network_graph_new", "data"),
            State("scenario", "data"),
            State("agent_study", "data"),
            State("user_timestamps", "data"),
        ],
    )
    def update_action(
        add_n_clicks,
        reset_n_clicks,
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
        network_graph_t,
        network_graph_t_next,
        network_graph_new,
        scenario,
        study_agent,
        timestamp,
    ):
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "reset_action":
            graph_div = dcc.Graph(figure=network_graph_t)
            return (
                None,
                "Compose some actions to study",
                graph_div,
                None,
                network_graph_t_next,
            )

        if add_n_clicks is None:
            raise PreventUpdate
        episode = make_episode(study_agent, scenario)
        if method_tab == "tab-0":
            # Dropdown
            if objet_tab == "tab-0":
                # Lines
                (line_ids,) = np.where(episode.line_names == selected_line)
                line_id = int(line_ids[0])
                side = "ex" if "ex" in ex_or_lines else "or"
                bus_number_lines = -1  # Disconnect
                if bus_lines == "Bus1":
                    bus_number_lines = 1
                elif bus_lines == "Bus2":
                    bus_number_lines = 2
                if topology_type_lines == "Set":
                    if target_lines == "Status":
                        if disc_rec_lines == "Reconnect":
                            action_dict = {"set_line_status": [(line_id, 1)]}
                        else:
                            # Disconnect
                            action_dict = {"set_line_status": [(line_id, -1)]}
                    else:
                        # Bus
                        action_dict = {
                            "set_bus": {
                                f"lines_{side}_id": [(line_id, bus_number_lines)]
                            }
                        }
                else:
                    # Change
                    if target_lines == "Status":
                        action_dict = {"change_line_status": [line_id]}
                    else:
                        # Bus
                        action_dict = {"change_bus": {f"lines_{side}_id": [line_id]}}
            elif objet_tab == "tab-1":
                # Loads
                (load_ids,) = np.where(episode.load_names == selected_load)
                load_id = load_ids[0]
                bus_number_loads = -1  # Disconnect
                if bus_loads == "Bus1":
                    bus_number_loads = 1
                elif bus_loads == "Bus2":
                    bus_number_loads = 2
                if topology_type_loads == "Set":
                    action_dict = {
                        "set_bus": {"loads_id": [(load_id, bus_number_loads)]}
                    }
                else:
                    # Change
                    action_dict = {"change_bus": {"loads_id": [load_id]}}
            else:
                # Gens
                (gen_ids,) = np.where(episode.prod_names == selected_gen)
                gen_id = int(
                    gen_ids[0]
                )  # gen_ids[0] is of type np.int64 which is not json serializable
                bus_number_gens = -1  # Disconnect
                if bus_gens == "Bus1":
                    bus_number_gens = 1
                elif bus_gens == "Bus2":
                    bus_number_gens = 2
                if action_type_gens == "Redispatch":
                    action_dict = {"redispatch": {gen_id: float(redisp_volume)}}
                else:
                    # Topology
                    if topology_type_gens == "Set":
                        action_dict = {
                            "set_bus": {"generators_id": [(gen_id, bus_number_gens)]}
                        }
                    else:
                        # Change
                        action_dict = {"change_bus": {"generators_id": [gen_id]}}
            if actions is None:
                actions = [action_dict]
            else:
                actions.append(action_dict)
        else:
            # Dict
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
                return actions, "", graph_div_child, action_dict, network_graph_t_next
            if "action_list" in action_dict:
                actions_for_textarea = action_dict["action_list"]
            else:
                actions_for_textarea = [action_dict]
            if actions is None:
                actions = actions_for_textarea
            else:
                actions.extend(actions_for_textarea)

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
        episode_reboot.load(
            env.backend,
            data=episode,
            agent_path=agents_dir + study_agent,
            name=episode.episode_name,
            env_kwargs=params_for_reboot,
        )
        t = episode.timestamps.index(timestamp)
        obs, reward, *_ = episode_reboot.go_to(t)
        act = PlayableAction()

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
            new_network_graph = network_graph_t_next

        try:
            json.dumps(actions)
        except Exception as ex:
            print("actions")
            print(actions)
        if method_tab == "tab-0":
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
        [Input("simulate_action", "n_clicks"), Input("tabs_network", "active_tab")],
        [
            State("actions", "data"),
            State("network_graph_new", "data"),
            State("network_graph_t+1", "data"),
            State("tabs-choose-assist-method", "active_tab"),
            State("simulation-assistant-store", "data"),
        ],
    )
    def simulate(
        simulate_n_clicks,
        active_tab_networks,
        actions,
        network_graph_new,
        network_graph_t_next,
        active_tab_choose_assist,
        simulation_assistant_store,
    ):
        if simulate_n_clicks is None or (
            actions is None and simulation_assistant_store is None
        ):
            raise PreventUpdate
        if active_tab_networks == "tab_new_network_state":
            if active_tab_choose_assist == "tab-assist-method":
                return dcc.Graph(
                    figure=go.Figure(
                        assistant.store_to_graph(simulation_assistant_store)
                    )
                )
            else:
                return dcc.Graph(figure=network_graph_new)
        elif active_tab_networks == "tab_old_network_state":
            return dcc.Graph(figure=network_graph_t_next)

    @app.callback(
        Output("simulation-assistant-store", "data"), [Input("assistant_store", "data")]
    )
    def transfer_assistant_store(data):
        """Necessary so that the store can be reach even when the assistant_store is
        not part of the view (e.g. when in choose mode)"""
        return data
