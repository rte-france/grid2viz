from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from src.app import app
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.grid2kpi.episode import observation_model, env_actions, consumption_profiles
from src.grid2kpi.manager import episode, make_episode, base_dir, indx, agent_ref


@app.callback(
    Output("input_env_charts", "figure"),
    [Input("input_env_selector", "value")],
    [State("input_env_charts", "figure")]
)
def load_summary_data(value, figure):
    if value is None:
        return figure
    if value is "1":
        figure["data"] = observation_model.get_load_trace_per_equipment()
    if value is "2":
        figure["data"] = observation_model.get_prod_trace_per_equipment()
    if value is "3":
        figure["data"] = observation_model.get_hazard_trace()
    if value is "4":
        figure["data"] = observation_model.get_maintenance_trace()
    return figure


@app.callback(
    Output("select_loads_for_tb", "options"),
    [Input('temporaryid', 'children')]
)
def update_select_loads(children):
    return [
        {'label': load, "value": load} for load in observation_model.episode.load_names
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
    [Output("inspection_table", "columns"), Output("inspection_table", "data")],
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
    cols_to_add = loads + prods
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
    return env_actions(observation_model.episode, which="hazards", kind="nb", aggr=True)


@app.callback(
    Output("nb_hazard_card", "children"),
    [Input('temporaryid', 'children')]
)
def update_card_hazard(children):
    return env_actions(observation_model.episode, which="maintenances", kind="nb", aggr=True)


@app.callback(
    [Output("overflow_graph", "figure"), Output("usage_rate_graph", "figure")],
    [Input('input_agent_selector', 'value')],
    [State("overflow_graph", "figure"), State("usage_rate_graph", "figure")]
)
def update_agent_ref_graph(value, figure_overflow, figure_usage):
    if value == agent_ref:
        raise PreventUpdate
    new_episode = make_episode(base_dir, value, indx)
    figure_overflow["data"] = observation_model.get_total_overflow_trace(new_episode)
    figure_usage["data"] = observation_model.get_usage_rate_trace(new_episode)
    return figure_overflow, figure_usage


@app.callback(
    Output("indicator_line_charts", "figure"),
    [Input('temporaryid', 'children')],
    [State("indicator_line_charts", "figure")]
)
def update_profile_conso_graph(children, figure):
    profiles = consumption_profiles(observation_model.episode)
    figure["data"] = [go.Scatter(x=profiles.index, y=profiles[col], name=col) for col in profiles.columns]
    return figure


@app.callback(
    Output("production_share_graph", "figure"),
    [Input('temporaryid', 'children')],
    [State("production_share_graph", "figure")]
)
def update_production_share_graph(children, figure):
    share_prod = observation_model.get_prod()
    figure["data"] = [
        go.Pie(labels=share_prod["equipment_name"], values=share_prod.groupby("equipment_name")["value"].sum())]
    return figure


@app.callback(
    [Output("date_range", "start_date"), Output("date_range", "end_date")],
    [Input('temporaryid', 'children')]
)
def update_date_range(children):
    return observation_model.episode.production["timestamp"].dt.date.values[0], \
           observation_model.episode.production["timestamp"].dt.date.values[-1]


def load_ref_agent_data():
    pass
