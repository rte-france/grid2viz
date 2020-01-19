from dash.dependencies import Output, Input, State

from src.app import app
from src.grid2viz.utils.graph_utils import relayout_callback


@app.callback(
    Output("timeseries_table_micro", "data"),
    [Input("timeseries_table", "data")]
)
def sync_timeseries_table(data):
    return data


@app.callback(
    Output("relayoutStoreMicro", "data"),
    [Input("cum_instant_reward_ts", "relayoutData"),
     Input("actions_ts", "relayoutData"),
     Input("interractive_graph", "relayoutData"),
     Input("temp_id_ts", "relayoutData"),
     Input("temp_id_heatmap", "relayoutData")],
    [State("relayoutStoreMicro", "data")]
)
def relayout_store_micro(*args):
    return relayout_callback(*args)
