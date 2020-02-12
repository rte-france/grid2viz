from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from src.app import app
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.grid2viz.utils.graph_utils import relayout_callback, get_axis_relayout
from src.grid2kpi.episode_analytics import observation_model, EpisodeTrace
from src.grid2kpi.episode_analytics.consumption_profiles import profiles_traces
from src.grid2kpi.episode_analytics.env_actions import env_actions
from src.grid2kpi.manager import episode, make_episode, base_dir, episode_name, agent_ref, prod_types, best_agents
from src.grid2kpi.episode_analytics.maintenances import duration_maintenances
from src.grid2viz.utils.perf_analyser import timeit


@app.callback(
    Output("relayoutStoreOverview", "data"),
    [Input("input_env_charts", "relayoutData"),
     Input("usage_rate_graph", "relayoutData"),
     Input("overflow_graph", "relayoutData")],
    [State("relayoutStoreOverview", "data")]
)
def relayout_store_overview(*args):
    return relayout_callback(*args)


@app.callback(
    [Output("input_assets_selector", "options"),
     Output("input_assets_selector", "value")],
    [Input("scen_overview_ts_switch", "value")],
    [State('scenario', 'data')]
)
def update_ts_graph_avail_assets(kind, scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)

    if kind in ["Hazards", "Maintenances"]:
        options, value = [{'label': line_name, 'value': line_name}
                          for line_name in [*best_agent_ep.line_names, 'total']], best_agent_ep.line_names[0]
    elif kind == 'Production':
        options = [{'label': prod_name,
                    'value': prod_name}
                   for prod_name in [*best_agent_ep.prod_names, *list(set(prod_types.values())), 'total']]
        value = best_agent_ep.prod_names[0]
    else:
        options = [{'label': load_name,
                    'value': load_name}
                   for load_name in [*best_agent_ep.load_names, 'total']]
        value = best_agent_ep.load_names[0]

    return options, value


@app.callback(
    Output("input_env_charts", "figure"),
    [Input("input_assets_selector", "value"),
     Input("relayoutStoreOverview", "data")],
    [State("input_env_charts", "figure"),
     State("scen_overview_ts_switch", "value"),
     State('scenario', 'data')]
)
def load_environments_ts(equipments, relayout_data_store, figure, kind, scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)

    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure
    if kind is None:
        return figure
    if isinstance(equipments, str):
        equipments = [equipments]  # to make pd.series.isin() work

    if kind == "Load":
        figure["data"] = EpisodeTrace.get_load_trace_per_equipment(best_agent_ep, equipments)
    if kind == "Production":
        figure["data"] = EpisodeTrace.get_all_prod_trace(best_agent_ep, prod_types, equipments)
    if kind == "Hazards":
        figure["data"] = EpisodeTrace.get_hazard_trace(best_agent_ep, equipments)
    if kind == "Maintenances":
        figure["data"] = EpisodeTrace.get_maintenance_trace(best_agent_ep, equipments)

    return figure


@app.callback(
    Output("select_loads_for_tb", "options"),
    [Input('temporaryid', 'children')]
)
def update_select_loads(children):
    return [
        {'label': load, "value": load} for load in [*episode.load_names, 'total']
    ]


@app.callback(
    Output("select_prods_for_tb", "options"),
    [Input('temporaryid', 'children')]
)
def update_select_prods(children):
    return [
        {'label': prod, "value": prod} for prod in episode.prod_names
    ]


@app.callback(
    [Output("inspection_table", "columns"),
     Output("inspection_table", "data")],
    [Input("select_loads_for_tb", "value"),
     Input("select_prods_for_tb", "value"),
     Input("temporaryid", "children")
     ],
    [State("inspection_table", "data")]
)
def update_table(loads, prods, children, data):
    if data is None:
        table = observation_model.init_table_inspection_data(episode)
        return [{"name": i, "id": i} for i in table.columns], table.to_dict('records')
    if loads is None:
        loads = []
    if prods is None:
        prods = []
    df = pd.DataFrame.from_records(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    cols_to_drop = []
    for col in df.columns[4:]:
        if col not in loads and col not in prods:
            cols_to_drop.append(col)
    cols_to_add = [col for col in loads + prods if col not in df.columns]
    df = df.drop(cols_to_drop, axis=1)
    if cols_to_add:
        df = df.merge(
            observation_model.get_prod_and_conso(episode)[cols_to_add], left_on="timestamp", right_index=True)
    cols = [{"name": i, "id": i} for i in df.columns]
    return cols, df.to_dict('records')


@app.callback(
    Output("nb_steps_card", "children"),
    [Input('scenario', 'data')]
)
def update_card_step(scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    return '{} / {}'.format(best_agent_ep.meta['nb_timestep_played'], best_agent_ep.meta['chronics_max_timestep'])


@app.callback(
    Output("nb_maintenance_card", "children"),
    [Input('scenario', 'data')]
)
def update_card_maintenance(scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    return env_actions(best_agent_ep, which="maintenances", kind="nb", aggr=True)


@app.callback(
    Output("nb_hazard_card", "children"),
    [Input('scenario', 'data')]
)
def update_card_hazard(scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    return env_actions(best_agent_ep, which="hazards", kind="nb", aggr=True)


@app.callback(
    Output("duration_maintenance_card", "children"),
    [Input('scenario', 'data')]
)
def update_card_duration_maintenances(scenario):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    return observation_model.get_duration_maintenances(best_agent_ep)


@app.callback(
    Output("agent_ref", "data"),
    [Input("input_agent_selector", "value")]
)
def update_selected_ref_agent(ref_agent):
    return ref_agent


@app.callback(
    [Output("overflow_graph", "figure"), Output("usage_rate_graph", "figure")],
    [Input('agent_ref', 'data'),
     Input("relayoutStoreOverview", "data")],
    [State("overflow_graph", "figure"), State("usage_rate_graph", "figure")]
)
def update_agent_ref_graph(ref_agent, relayout_data_store, figure_overflow, figure_usage):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout_usage = figure_usage["layout"]
        new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
        if new_axis_layout is not None:
            layout_usage.update(new_axis_layout)
            figure_overflow["layout"].update(new_axis_layout)
            return figure_overflow, figure_usage
    if ref_agent == agent_ref:
        new_episode = episode
    else:
        new_episode = make_episode(ref_agent, episode_name)
    figure_overflow["data"] = new_episode.total_overflow_trace
    figure_usage["data"] = new_episode.usage_rate_trace
    return figure_overflow, figure_usage


@app.callback(
    Output("indicator_line_charts", "figure"),
    [Input('scenario', 'data')],
    [State("indicator_line_charts", "figure")]
)
def update_profile_conso_graph(scenario, figure):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    figure["data"] = profiles_traces(best_agent_ep, freq="30T")
    return figure


@app.callback(
    Output("production_share_graph", "figure"),
    [Input('scenario', 'data')],
    [State("production_share_graph", "figure")]
)
def update_production_share_graph(scenario, figure):
    best_agent_ep = make_episode(best_agents[scenario]['agent'], scenario)
    share_prod = EpisodeTrace.get_prod_share_trace(best_agent_ep, prod_types)
    figure["data"] = share_prod
    return figure


@app.callback(
    [Output("date_range", "start_date"), Output("date_range", "end_date")],
    [Input('temporaryid', 'children')]
)
def update_date_range(children):
    return episode.production["timestamp"].dt.date.values[0], \
           episode.production["timestamp"].dt.date.values[-1]
