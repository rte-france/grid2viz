from dash.dependencies import Input, Output, State
from src.app import app
import plotly.graph_objects as go

from src.grid2kpi.manager import episode, make_episode, base_dir, indx, agent_ref
from src.grid2kpi.episode import observation_model
from src.grid2kpi.episode import actions_model


@app.callback(
    Output("cumulated_rewards_timeserie", "figure"),
    [Input('overview_line_id', 'children')],
    [State("cumulated_rewards_timeserie", "figure")]
)
def load_reward_data_scatter(children, figure):
    figure['data'] = observation_model.get_df_rewards_trace(observation_model.episode)
    figure['layout'] = {**figure['layout'], 'yaxis2': {'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }
    return figure


@app.callback(
    Output("store", "cur_agent_log"),
    [Input('agent_log_selector', 'value')],
)
def update_agent_log(value):
    # hack to make sure the episode is loaded before all other callbcks descending agent_log_selector
    episode = make_episode(base_dir, value, indx)
    return value


@app.callback(
    [Output("overflow_graph_study", "figure"), Output("usage_rate_graph_study", "figure")],
    [Input('store', 'cur_agent_log')],
    [State("overflow_graph_study", "figure"), State("usage_rate_graph_study", "figure")]
)
def update_agent_log_graph(cur_agent_log, figure_overflow, figure_usage):
    new_episode = make_episode(base_dir, cur_agent_log, indx)
    figure_overflow["data"] = observation_model.get_total_overflow_trace(
        new_episode)
    figure_usage["data"] = observation_model.get_usage_rate_trace(new_episode)
    return figure_overflow, figure_usage


@app.callback(
    [Output("inspector_datable", "columns"), Output("inspector_datable", "data")],
    [Input('store', 'cur_agent_log')],
    [State("inspector_datable", "data")]
)
def update_agent_log_action_table(cur_agent_log, data):
    new_episode = make_episode(base_dir, cur_agent_log, indx)
    table = new_episode.action_data
    return [{"name": i, "id": i} for i in table.columns], table.to_dict("record")


@app.callback(
    [Output("distribution_substation_action_chart", "figure"), Output("distribution_line_action_chart", "figure")],
    [Input('store', 'cur_agent_log')],
    [State("distribution_substation_action_chart", "figure"), State("distribution_line_action_chart", "figure")]
)
def update_agent_log_action_graphs(cur_agent_log, figure_sub, figure_switch_line):
    new_episode = make_episode(base_dir, cur_agent_log, indx)
    figure_sub["data"] = actions_model.get_action_set_topo_trace(new_episode)
    # figure_line["data"] = actions_model.get_action_set_line_trace(new_episode)
    # figure_bus["data"] = actions_model.get_action_change_bus_trace(new_episode)
    figure_switch_line["data"] = actions_model.get_action_switch_line_trace(new_episode)
    return figure_sub, figure_switch_line
