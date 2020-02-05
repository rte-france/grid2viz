from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd

from src.app import app
from src.grid2viz.utils.perf_analyser import whoami, timeit


@app.callback(
    Output("store", "data"),
    [Input("load_data", "n_clicks")]
)
def update_data_store(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    data = pd.DataFrame(data=[[0, 1], [-2, -1]])
    return data.to_json(orient="split")


@app.callback(
    Output("graph1", "figure"),
    [Input("store", "data")],
    [State("graph1", "figure")]
)
def update_graph1(store, figure):
    if figure is None or store is None:
        raise PreventUpdate
    graph_data = figure["data"]
    data = pd.read_json(store, orient="split")
    for col, trace in zip(data.columns, graph_data):
        trace.update(dict(y=data[col]))
    return figure


@app.callback(
    Output("graph2", "figure"),
    [Input("store", "data")],
    [State("graph2", "figure")]
)
def update_graph2(store, figure):
    if figure is None or store is None:
        raise PreventUpdate
    graph_data = figure["data"]
    data = -pd.read_json(store, orient="split")
    for col, trace in zip(data.columns, graph_data):
        trace.update(dict(y=data[col]))
    return figure
