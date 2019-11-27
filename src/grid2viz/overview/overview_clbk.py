from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from src.app import app
import numpy as np  # TODO delete after getting the back end working

# TODO remove this when callback created
N = 100
random_x = np.linspace(0, 1, N)
random_y0 = np.random.randn(N) + 5
random_y1 = np.random.randn(N)
random_y2 = np.random.randn(N)

@app.callback(
    Output("indicator_line_charts", "figure"),
    [Input("store", "data")],
    [State("indicator_line_charts", "figure")]
)
def load_indicators_data(store, figure):
    print("test")
    if figure is None or store is None:
        raise PreventUpdate
    data = [dict(
        x=random_x, y=random_y1
    )]
    return {'data': data}



def load_summary_data():
    pass


def load_ref_agent_data():
    pass
