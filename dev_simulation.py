import json

import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dill
import numpy as np
from dash import Dash, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from grid2op.Action import PlayableAction
from grid2op.Episode import EpisodeData, EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters
from grid2op.PlotGrid import PlotPlotly

from grid2viz.src.utils.serialization import NoIndent, MyEncoder

# We need to create app before importing the rest of the project as it uses @app decorators
font_awesome = [
    {
        "href": "https://use.fontawesome.com/releases/v5.8.1/css/all.css",
        "rel": "stylesheet",
        "integrity": "sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf",
        "crossorigin": "anonymous",
    }
]
app = Dash("simulation", external_stylesheets=[dbc.themes.BOOTSTRAP, *font_awesome])

scenario = "000"
agent = "do-nothing-baseline"
agent_dir = "D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/" + agent
path = r"D:\Projects\RTE-Grid2Viz\grid2viz\grid2viz\data\agents\_cache\000\do-nothing-baseline.dill"
with open(path, "rb") as f:
    episode = dill.load(f)
episode_data = EpisodeData.from_disk(agent_dir, scenario)
episode.decorate(episode_data)

network_graph_factory = PlotPlotly(
    grid_layout=episode.observation_space.grid_layout,
    observation_space=episode.observation_space,
    responsive=True,
)

t = 0
network_graph = network_graph_factory.plot_obs(observation=episode.observations[t])


def lines_tab_layout(episode):
    return [
        html.P("Choose a line to act on:", className="mt-1"),
        dac.Select(
            id="select_lines_simulation",
            options=[
                {"label": line_name, "value": line_name}
                for line_name in episode.line_names
            ],
            mode="default",
            value=episode.line_names[0],
        ),
        html.P("Choose an action type:", className="mt-1"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_lines",
            buttonStyle="solid",
        ),
        html.P("Choose a target type:", className="mt-1"),
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
        html.P("Choose an action type:"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_loads",
            buttonStyle="solid",
        ),
        html.P("Choose an action:", className="mt-1"),
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
        html.P("Choose an action type:"),
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


def choose_assist_line(episode, network_graph):
    return html.Div(
        id="choose_assist_line",
        className="lineBlock card",
        children=[
            html.H4("Choose or Assist"),
            html.Div(
                className="card-body row",
                children=[
                    html.Div(
                        className="col-7",
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
                    html.Div(
                        className="col-5",
                        children=[
                            dbc.Tabs(
                                children=[
                                    dbc.Tab(
                                        label="Choose",
                                        labelClassName="fas fa-user",
                                        children=[
                                            dbc.Tabs(
                                                id="tab_method",
                                                children=[
                                                    dbc.Tab(
                                                        label="Dropdowns",
                                                        children=[
                                                            dbc.Tabs(
                                                                id="tab_object",
                                                                children=[
                                                                    dbc.Tab(
                                                                        label="Lines",
                                                                        children=lines_tab_layout(
                                                                            episode
                                                                        ),
                                                                    ),
                                                                    dbc.Tab(
                                                                        label="Loads",
                                                                        children=loads_tab_layout(
                                                                            episode
                                                                        ),
                                                                    ),
                                                                    dbc.Tab(
                                                                        label="Gens",
                                                                        children=gens_tab_layout(
                                                                            episode
                                                                        ),
                                                                    ),
                                                                ],
                                                            )
                                                        ],
                                                    ),
                                                    dbc.Tab(
                                                        label="Dict",
                                                        children=[
                                                            html.P(
                                                                "Enter the action dictionary:"
                                                            ),
                                                            dbc.Textarea(
                                                                id="textarea",
                                                                className="mb-3",
                                                                placeholder='{"set_line_status": []}',
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                    ),
                                    dbc.Tab(
                                        label="Assist",
                                        labelClassName="fas fa-robot",
                                        children=["content"],
                                    ),
                                ]
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
                            html.P(id="action_info", className="more-info-table"),
                        ],
                    ),
                ],
            ),
        ],
    )


def compare_line(network_graph):
    return html.Div(
        id="compare_line",
        className="lineBlock card",
        children=[
            html.H4("Compare"),
            html.Div(
                className="card-body row",
                children=[
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
                                                    children=[
                                                        dbc.Tab(
                                                            label="New State t+1",
                                                            tab_id="tab_new_network_state",
                                                        ),
                                                        dbc.Tab(
                                                            label="Old State t+1",
                                                            tab_id="tab_old_network_state",
                                                        ),
                                                    ]
                                                ),
                                            ),
                                            dbc.CardBody(
                                                id="card_body_network",
                                                children=[
                                                    dcc.Graph(
                                                        id="network_state",
                                                        figure=network_graph,
                                                    ),
                                                ],
                                            ),
                                        ]
                                    )
                                ],
                            ),
                        ],
                    ),
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
                                                        children="0",
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
                                                        children="0",
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
                                                        children="0",
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
                                                        children="0",
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
                ],
            ),
        ],
    )


@app.callback(
    [
        Output("actions", "data"),
        Output("action_info", "children"),
        Output("graph_div", "children"),
        Output("textarea", "value"),
        # Output("network_graph_new", "data"),
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
        # State("network_graph_new", "data"),
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
    # network_graph_new,
):
    ctx = callback_context

    if not ctx.triggered:
        raise PreventUpdate
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "reset_action":
        graph_div = dcc.Graph(figure=network_graph_t)
        return None, "", graph_div, None  # , network_graph_t

    if add_n_clicks is None:
        raise PreventUpdate
    if method_tab == "tab-0":
        # Dropdown
        if objet_tab == "tab-0":
            # Lines
            (line_ids,) = np.where(episode_data.line_names == selected_line)
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
                        "set_bus": {f"lines_{side}_id": [(line_id, bus_number_lines)]}
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
            (load_ids,) = np.where(episode_data.load_names == selected_load)
            load_id = load_ids[0]
            bus_number_loads = -1  # Disconnect
            if bus_loads == "Bus1":
                bus_number_loads = 1
            elif bus_loads == "Bus2":
                bus_number_loads = 2
            if topology_type_loads == "Set":
                action_dict = {"set_bus": {"loads_id": [(load_id, bus_number_loads)]}}
            else:
                # Change
                action_dict = {"change_bus": {"loads_id": [load_id]}}
        else:
            # Gens
            (gen_ids,) = np.where(episode_data.prod_names == selected_gen)
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
            action_dict = json.loads(action_dict.replace("(", "[").replace(")", "]"))
        except json.decoder.JSONDecodeError as ex:
            import traceback

            graph_div_child = html.Div(
                children=traceback.format_exc(), className="more-info-table"
            )
            return actions, "", graph_div_child, action_dict  # , network_graph_new
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
        key: value for key, value in params_for_runner.items() if key in params_to_fetch
    }
    params_for_reboot["parameters"] = p

    episode_reboot = EpisodeReboot.EpisodeReboot()
    agent_path = (
        r"D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/do-nothing-baseline"
    )
    episode_reboot.load(
        env.backend,
        data=episode,
        agent_path=agent_path,
        name=episode.episode_name,
        env_kwargs=params_for_reboot,
    )
    current_time_step = 0
    obs, reward, *_ = episode_reboot.go_to(1)
    act = PlayableAction()

    for action in actions:
        act.update(action)
    obs, *_ = obs.simulate(action=act, time_step=0)
    try:
        graph_div_child = dcc.Graph(figure=network_graph_t)
        new_network_graph = network_graph_factory.plot_obs(observation=obs)
    except ValueError:
        import traceback

        graph_div_child = html.Div(
            children=traceback.format_exc(), className="more-info-table"
        )

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
            # new_network_graph,
        )
    else:
        actions_for_textarea = dict(
            action_list=[*[NoIndent(action) for action in actions[:-1]], actions[-1]]
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
            # new_network_graph,
        )


@app.callback(
    [
        Output("radio_disc_rec_lines", "className"),
        Output("radio_target_lines", "className"),
        Output("radio_bus_lines", "className"),
        Output("radio_ex_or_lines", "className"),
    ],
    [Input("radio_topology_type_lines", "value"), Input("radio_target_lines", "value")],
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
    [State("actions", "data")],
)
def simulate(simulate_n_clicks, actions):

    if simulate_n_clicks is None or actions is None:
        raise PreventUpdate
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
        key: value for key, value in params_for_runner.items() if key in params_to_fetch
    }
    params_for_reboot["parameters"] = p

    episode_reboot = EpisodeReboot.EpisodeReboot()
    agent_path = (
        r"D:/Projects/RTE-Grid2Viz/grid2viz/grid2viz/data/agents/do-nothing-baseline"
    )
    episode_reboot.load(
        env.backend,
        data=episode,
        agent_path=agent_path,
        name=episode.episode_name,
        env_kwargs=params_for_reboot,
    )
    current_time_step = 0
    obs, reward, *_ = episode_reboot.go_to(1)
    act = PlayableAction()

    for action in actions:
        act.update(action)
    obs, *_ = obs.simulate(action=act, time_step=0)
    try:
        graph_div_child = dcc.Graph(
            figure=network_graph_factory.plot_obs(observation=obs)
        )
    except ValueError:
        import traceback

        graph_div_child = html.Div(
            children=traceback.format_exc(), className="more-info-table"
        )
    return graph_div_child


app.layout = html.Div(
    id="simulation_page",
    children=[
        dcc.Store(id="actions", storage_type="memory"),
        dcc.Store(id="network_graph_t", storage_type="memory", data=network_graph),
        dcc.Store(
            id="network_graph_t+1",
            storage_type="memory",
            data=network_graph_factory.plot_obs(
                observation=episode.observations[t + 1]
            ),
        ),
        dcc.Store(
            id="network_graph_new",
            storage_type="memory",
        ),
        choose_assist_line(episode, network_graph),
        compare_line(network_graph),
    ],
)

if __name__ == "__main__":
    app.run_server(port=8008)
