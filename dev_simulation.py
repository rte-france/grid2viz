import json

from alphaDeesp.expert_operator import expert_operator
from alphaDeesp.core.grid2op.Grid2opSimulation import (
    Grid2opSimulation,
    score_changes_between_two_observations,
)
import dash_antd_components as dac
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash_table import DataTable
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
import plotly.graph_objects as go

from grid2viz.src.utils.serialization import NoIndent, MyEncoder
from grid2viz.src.simulation.simulation_assist import BaseAssistant

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

t = 1
network_graph = network_graph_factory.plot_obs(observation=episode.observations[t])


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

obs, reward, *_ = episode_reboot.go_to(t)

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


class Assist(BaseAssistant):
    def __init__(self):
        super().__init__()

    def layout(self):
        return html.Div(
            [
                dcc.Store(id="assistant_store", data="Toto"),
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
            Output("expert-results", "children"),
            [Input("assist-button", "n_clicks")],
        )
        def evaluate_expert_system(n_clicks):
            if n_clicks is None:
                raise PreventUpdate
            return DataTable(
                id="table",
                columns=[{"name": i, "id": i} for i in expert_system_results.columns],
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
            )

        @app.callback(
            [
                Output("assistant_store", "data"),
                Output("assist-action-info", "children"),
            ],
            [Input("table", "selected_rows")],
        )
        def select_action(selected_rows):
            if selected_rows is None:
                raise PreventUpdate
            selected_row = selected_rows[0]
            action = actions[selected_row]
            # Temporary implementation for testing purposes
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
            agent_path = path
            episode_reboot.load(
                env.backend,
                data=episode,
                agent_path=agent_path,
                name=episode.episode_name,
                env_kwargs=params_for_reboot,
            )
            obs, reward, *_ = episode_reboot.go_to(t)
            obs, *_ = obs.simulate(action=action, time_step=0)
            try:
                new_network_graph = network_graph_factory.plot_obs(observation=obs)
            except ValueError:
                import traceback

                new_network_graph = traceback.format_exc()

            return new_network_graph, str(action)


assistant = Assist()


def lines_tab_layout(episode):
    return [
        html.P("Choose a line to act on:", className="my-2"),
        dac.Select(
            id="select_lines_simulation",
            options=[
                {"label": line_name, "value": line_name}
                for line_name in episode.line_names
            ],
            mode="default",
            value=episode.line_names[0],
        ),
        html.P("Choose an action type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_lines",
            buttonStyle="solid",
        ),
        html.P("Choose a target type:", className="my-2"),
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
        html.P("Choose an action type:", className="my-2"),
        dac.Radio(
            options=[
                {"label": "Set", "value": "Set"},
                {"label": "Change", "value": "Change"},
            ],
            value="Set",
            id="radio_topology_type_loads",
            buttonStyle="solid",
        ),
        html.P("Choose an action:", className="my-2"),
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
        html.P("Choose an action type:", className="my-2"),
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


def choose_tab_content(episode):
    return [
        dbc.Tabs(
            id="tab_method",
            className="nav-fill",
            children=[
                dbc.Tab(
                    label="Dropdowns",
                    children=[
                        dbc.Tabs(
                            id="tab_object",
                            className="nav-fill",
                            children=[
                                dbc.Tab(
                                    label="Lines",
                                    children=lines_tab_layout(episode),
                                ),
                                dbc.Tab(
                                    label="Loads",
                                    children=loads_tab_layout(episode),
                                ),
                                dbc.Tab(
                                    label="Gens",
                                    children=gens_tab_layout(episode),
                                ),
                            ],
                        )
                    ],
                ),
                dbc.Tab(
                    label="Dict",
                    children=[
                        html.P("Enter the action dictionary:"),
                        dbc.Textarea(
                            id="textarea",
                            className="mb-3",
                            placeholder='{"set_line_status": []}',
                        ),
                    ],
                ),
            ],
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
        html.P(
            id="action_info",
            className="more-info-table",
            children="Compose some actions to study",
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
                        id="",
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
                        className="col-5 chooseAssist",
                        children=[
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        dbc.Tabs(
                                            id="tabs-choose-assist-method",
                                            card=True,
                                            active_tab="tab-choose-method",
                                            children=[
                                                dbc.Tab(
                                                    label="Choose",
                                                    tab_id="tab-choose-method",
                                                ),
                                                dbc.Tab(
                                                    label="Assist",
                                                    tab_id="tab-assist-method",
                                                ),
                                            ],
                                        )
                                    ),
                                    dbc.CardBody(
                                        html.Div(id="tabs-choose-assist-method-content")
                                    ),
                                ]
                            ),
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
                                                    id="tabs_network",
                                                    children=[
                                                        dbc.Tab(
                                                            label="New State t+1",
                                                            tab_id="tab_new_network_state",
                                                        ),
                                                        dbc.Tab(
                                                            label="Old State t+1",
                                                            tab_id="tab_old_network_state",
                                                        ),
                                                    ],
                                                    active_tab="tab_new_network_state",
                                                ),
                                            ),
                                            dbc.CardBody(
                                                id="card_body_network",
                                                children=[
                                                    "Compose an action above and then simulate it."
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
    Output("tabs-choose-assist-method-content", "children"),
    [Input("tabs-choose-assist-method", "active_tab")],
)
def simulation_method_tab_content(active_tab):
    if active_tab is None:
        raise PreventUpdate
    if active_tab == "tab-choose-method":
        return choose_tab_content(episode)
    elif active_tab == "tab-assist-method":
        return assistant.checked_layout(choose_tab_content(episode))


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
    agent_path = path
    episode_reboot.load(
        env.backend,
        data=episode,
        agent_path=agent_path,
        name=episode.episode_name,
        env_kwargs=params_for_reboot,
    )
    current_time_step = 0
    obs, reward, *_ = episode_reboot.go_to(t)
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
            new_network_graph,
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
    simualtion_assistant_store,
):
    if simulate_n_clicks is None or (
        actions is None and simualtion_assistant_store is None
    ):
        raise PreventUpdate
    if active_tab_networks == "tab_new_network_state":
        if active_tab_choose_assist == "tab-assist-method":
            return dcc.Graph(figure=go.Figure(simualtion_assistant_store))
        else:
            return dcc.Graph(figure=network_graph_new)
    elif active_tab_networks == "tab_old_network_state":
        return dcc.Graph(figure=network_graph_t_next)


@app.callback(
    Output("simulation-assistant-store", "data"), [Input("assistant_store", "data")]
)
def transfer_assistant_store(data):
    """Necessary so that the store can be reach evenn when the assistant_store is
    not part of the view (e.g. when in choose mode)"""
    return data


app.layout = html.Div(
    id="simulation_page",
    children=[
        dcc.Store(id="actions", storage_type="memory"),
        dcc.Store(id="simulation-assistant-store", storage_type="memory"),
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


assistant.register_callbacks(app)

if __name__ == "__main__":
    app.run_server(port=8008)
