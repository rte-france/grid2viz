from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from src.app import app
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.grid2viz.utils.graph_utils import relayout_callback, get_axis_relayout
from src.grid2kpi.episode import observation_model, env_actions, profiles_traces
from src.grid2kpi.manager import episode, make_episode, base_dir, indx, agent_ref, prod_types
from src.grid2kpi.episode.maintenances import duration_maintenances


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
    [Input("scen_overview_ts_switch", "value")]
)
def update_ts_graph_avail_assets(kind):
    if kind in ["Hazards", "Maintenances"]:
        options, value = [{'label': line_name, 'value': line_name}
                          for line_name in [*episode.line_names, 'total']], episode.line_names[0]
    elif kind == 'Production':
        options = [{'label': prod_name,
                    'value': prod_name}
                   for prod_name in [*episode.prod_names, *list(set(prod_types.values())), 'total']]
        value = episode.prod_names[0]
    else:
        options = [{'label': load_name,
                    'value': load_name}
                   for load_name in [*episode.load_names, 'total']]
        value = episode.load_names[0]

    return options, value


@app.callback(
    Output("input_env_charts", "figure"),
    [Input("input_assets_selector", "value"),
     Input("relayoutStoreOverview", "data")],
    [State("input_env_charts", "figure"),
     State("scen_overview_ts_switch", "value")]
)
def load_summary_data(equipments, relayout_data_store, figure, kind):
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
        figure["data"] = observation_model.get_load_trace_per_equipment(
            equipments)
    if kind == "Production":
        figure["data"] = observation_model.get_all_prod_trace(equipments)
    if kind == "Hazards":
        figure["data"] = observation_model.get_hazard_trace(equipments)
    if kind == "Maintenances":
        figure["data"] = observation_model.get_maintenance_trace(equipments)

    return figure


@app.callback(
    Output("select_loads_for_tb", "options"),
    [Input('temporaryid', 'children')]
)
def update_select_loads(children):
    return [
        {'label': load, "value": load} for load in [*observation_model.episode.load_names, 'total']
    ]


@app.callback(
    Output("select_prods_for_tb", "options"),
    [Input('temporaryid', 'children')]
)
def update_select_prods(children):
    return [
        {'label': prod, "value": prod} for prod in observation_model.episode.prod_names
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
        table = observation_model.init_table_inspection_data()
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
            observation_model.get_prod_and_conso()[cols_to_add], left_on="timestamp", right_index=True)
    cols = [{"name": i, "id": i} for i in df.columns]
    return cols, df.to_dict('records')


@app.callback(
    Output("nb_steps_card", "children"),
    [Input('temporaryid', 'children')]
)
def update_card_step(children):
    return len(observation_model.episode.observations)


@app.callback(
    Output("nb_maintenance_card", "children"),
    [Input('temporaryid', 'children')]
)
def update_card_maintenance(children):
    return env_actions(observation_model.episode, which="maintenances", kind="nb", aggr=True)


@app.callback(
    Output("nb_hazard_card", "children"),
    [Input('temporaryid', 'children')]
)
def update_card_hazard(children):
    return env_actions(observation_model.episode, which="hazards", kind="nb", aggr=True)


@app.callback(
    Output("duration_maintenance_card", "children"),
    [Input('temporaryid', 'children')]
)
def update_card_duration_maintenances(children):
    return observation_model.get_duration_maintenances()


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
        new_episode = make_episode(base_dir, ref_agent, indx)
    figure_overflow["data"] = observation_model.get_total_overflow_trace(
        new_episode)
    figure_usage["data"] = observation_model.get_usage_rate_trace(new_episode)
    return figure_overflow, figure_usage


@app.callback(
    Output("indicator_line_charts", "figure"),
    [Input('temporaryid', 'children')],
    [State("indicator_line_charts", "figure")]
)
def update_profile_conso_graph(children, figure):
    figure["data"] = profiles_traces(observation_model.episode, freq="30T")
    return figure


@app.callback(
    Output("production_share_graph", "figure"),
    [Input('temporaryid', 'children')],
    [State("production_share_graph", "figure")]
)
def update_production_share_graph(children, figure):
    share_prod = observation_model.get_prod_share_trace()
    figure["data"] = share_prod
    return figure


@app.callback(
    [Output("date_range", "start_date"), Output("date_range", "end_date")],
    [Input('temporaryid', 'children')]
)
def update_date_range(children):
    return observation_model.episode.production["timestamp"].dt.date.values[0], \
        observation_model.episode.production["timestamp"].dt.date.values[-1]
