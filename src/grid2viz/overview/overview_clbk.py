from dash.dependencies import Input, Output, State
from src.app import app
import numpy as np
from src.grid2kpi.episode import observation_model

# TODO remove this when callback created
N = 100
random_x = np.linspace(0, 1, N)
random_y0 = np.random.randn(N) + 5
random_y1 = np.random.randn(N)
random_y2 = np.random.randn(N)

active_load_trace = observation_model.get_load_trace_per_equipment()
active_prod_trace = observation_model.get_prod_trace_per_equipment()


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
    return figure


def load_ref_agent_data():
    pass
