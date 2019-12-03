from dash.dependencies import Input, Output, State
from src.app import app
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from src.grid2kpi.episode import observation_model, env_actions

# TODO remove this when callback created
N = 100
random_x = np.linspace(0, 1, N)
random_y0 = np.random.randn(N) + 5
random_y1 = np.random.randn(N)
random_y2 = np.random.randn(N)

episode = observation_model.episode

active_load_trace = observation_model.get_load_trace_per_equipment()
active_prod_trace = observation_model.get_prod_trace_per_equipment()

productions = pd.pivot_table(
    episode.production, index="timestamp", values="value", 
    columns=["equipment_name"]
)

loads = pd.pivot_table(
    episode.load, index="timestamp", values="value", 
    columns=["equipment_name"]
)

prods_and_loads = productions.merge(loads, left_index=True, right_index=True)

ts_hazards_by_line = env_actions(
    episode, which="hazards", kind="ts", aggr=False) 
ts_maintenances_by_line = env_actions(
    episode, which="maintenances", kind="ts", aggr=False)


def load_indicators_data(data, figure):
    pass


@app.callback(
    Output("input_env_charts", "figure"),
    [Input("input_env_selector", "value")],
    [State("input_env_charts", "figure")]
)
def load_summary_data(value, figure):
    if value is None:
        return figure
    if value is "1":
        figure["data"] = active_load_trace
    if value is "2":
        figure["data"] = active_prod_trace
    if value is "3":
        figure["data"] = [
            go.Scatter(x=ts_hazards_by_line.index, y=ts_hazards_by_line[line],
                       name=line)
            for line in ts_hazards_by_line.columns            
    ]
    if value is "4":
        figure["data"] = [
            go.Scatter(x=ts_maintenances_by_line.index, 
                       y=ts_maintenances_by_line[line],
                       name=line)
            for line in ts_maintenances_by_line.columns            
    ]
    return figure


@app.callback(
    [Output("inspection_table", "columns"), Output("inspection_table", "data")], 
    [Input("select_loads_for_tb", "value"), 
     Input("select_prods_for_tb", "value"),],
    [State("inspection_table", "data")]
)
def update_table(loads, prods, data):
    if loads is None: loads = []
    if prods is None: prods = []
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
            prods_and_loads[cols_to_add], left_on="timestamp", right_index=True)
    cols = [{"name": i, "id": i} for i in df.columns]
    return cols, df.to_dict('records')


def load_ref_agent_data():
    pass
