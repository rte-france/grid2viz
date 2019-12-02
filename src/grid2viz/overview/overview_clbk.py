from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from src.app import app
import numpy as np

# TODO remove this when callback created
N = 100
random_x = np.linspace(0, 1, N)
random_y0 = np.random.randn(N) + 5
random_y1 = np.random.randn(N)
random_y2 = np.random.randn(N)


def load_indicators_data(data, figure):
    pass


@app.callback(
    Output("input_env_charts", "figure"),
    [Input("input_env_selector", "value")]
)
def load_summary_data(value):
    print(value)
    return {'data': [go.Scatter(x=random_x, y=random_y0)]}


def load_ref_agent_data():
    pass
