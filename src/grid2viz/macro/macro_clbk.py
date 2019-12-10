from dash.dependencies import Input, Output, State
from src.app import app
import plotly.graph_objects as go

from src.grid2kpi.episode import observation_model


@app.callback(
    Output("cumulated_rewards_timeserie", "figure"),
    [Input('overview_line_id', 'children')],
    [State("cumulated_rewards_timeserie", "figure")]
)
def load_reward_data_scatter(children, figure):
    figure['data'] = observation_model.get_df_rewards_trace(observation_model.episode)
    return figure
