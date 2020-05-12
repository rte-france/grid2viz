"""
    This files handles the generic information about the agent of reference of the selected scenario
    and let choose and compute study agent information.
"""
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from grid2viz.app import app
from grid2viz.src.manager import make_episode
from grid2viz.src.kpi import EpisodeTrace
from grid2viz.src.kpi import actions_model
from grid2viz.src.utils.graph_utils import get_axis_relayout, relayout_callback
from grid2viz.src.kpi.maintenances import (hist_duration_maintenances)

from grid2viz.src.utils.common_graph import make_action_ts, make_rewards_ts


@app.callback(
    Output("cumulated_rewards_timeserie", "figure"),
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("cumulated_rewards_timeserie", "figure"),
     State("agent_ref", "data"),
     State("scenario", "data")]
)
def load_reward_data_scatter(study_agent, relayout_data_store, figure, ref_agent, scenario):
    """Compute and  create figure with instant and cumulated rewards of the study and ref agent"""
    layout = figure["layout"]
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    return make_rewards_ts(study_agent, ref_agent, scenario, layout)


@app.callback(
    Output("agent_study_pie_chart", "figure"),
    [Input('agent_study', 'data')],
    [State("agent_study_pie_chart", "figure"),
     State("scenario", "data")]
)
def update_action_repartition_pie(study_agent, figure, scenario):
    new_episode = make_episode(study_agent, scenario)
    figure['data'] = action_repartition_pie(new_episode)
    return figure


def action_repartition_pie(agent):
    nb_actions = agent.action_data_table[['action_line', 'action_subs']].sum()
    return [go.Pie(
        labels=["Actions on Lines", "Actions on Substations"],
        values=[nb_actions["action_line"], nb_actions["action_subs"]]
    )]


@app.callback(
    Output("maintenance_duration", "figure"),
    [Input('agent_study', 'data')],
    [State("maintenance_duration", "figure"),
     State("scenario", "data")]
)
def maintenance_duration_hist(study_agent, figure, scenario):
    new_episode = make_episode(study_agent, scenario)
    figure['data'] = [go.Histogram(
        x=hist_duration_maintenances(new_episode)
    )]
    return figure


@app.callback(
    Output("timeseries_table", "data"),
    [Input("cumulated_rewards_timeserie", "clickData"),
     Input("agent_log_selector", "value")],
    [State("timeseries_table", "data"),
     State("agent_study", "data")]
)
def add_timestamp(click_data, new_agent, data, agent_stored):
    if new_agent != agent_stored or click_data is None:
        return []
    if data is None:
        data = []
    new_data = {"Timestamps": click_data["points"][0]["x"]}
    if new_data not in data:
        data.append(new_data)
    return data


@app.callback(
    Output("user_timestamps_store", "data"),
    [Input("timeseries_table", "data")]
)
def update_user_timestamps_store(timestamps):
    if timestamps is None:
        raise PreventUpdate
    return [dict(label=timestamp["Timestamps"], value=timestamp["Timestamps"])
            for timestamp in timestamps]


@app.callback(
    Output("relayoutStoreMacro", "data"),
    [Input("usage_rate_graph_study", "relayoutData"),
     Input("action_timeserie", "relayoutData"),
     Input("overflow_graph_study", "relayoutData"),
     Input("cumulated_rewards_timeserie", "relayoutData")],
    [State("relayoutStoreMacro", "data")]
)
def relayout_store(*args):
    return relayout_callback(*args)


@app.callback(
    [Output("indicator_score_output", "children"),
     Output("indicator_nb_overflow", "children"),
     Output("indicator_nb_action", "children")],
    [Input('agent_study', 'data'),
     Input("scenario", "data")]
)
def update_nbs(study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    score = get_score_agent(new_episode)
    nb_overflow = get_nb_overflow_agent(new_episode)
    nb_action = get_nb_action_agent(new_episode)

    return score, nb_overflow, nb_action


def get_score_agent(agent):
    score = agent.meta["cumulative_reward"]
    return round(score)


def get_nb_overflow_agent(agent):
    return agent.total_overflow_ts["value"].sum()


def get_nb_action_agent(agent):
    return agent.action_data_table[['action_line', 'action_subs']].sum(
        axis=1).sum()


@app.callback(
    Output("agent_study", "data"),
    [Input('agent_log_selector', 'value')],
    [State("agent_study", "data"),
     State("scenario", "data")],
)
def update_study_agent(study_agent, stored_agent, scenario):
    if study_agent == stored_agent:
        raise PreventUpdate
    make_episode(study_agent, scenario)
    return study_agent


@app.callback(
    [Output("overflow_graph_study", "figure"), Output(
        "usage_rate_graph_study", "figure")],
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("overflow_graph_study", "figure"),
     State("usage_rate_graph_study", "figure"),
     State("scenario", "data")]
)
def update_agent_log_graph(study_agent, relayout_data_store, figure_overflow, figure_usage, scenario):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout_usage = figure_usage["layout"]
        new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
        if new_axis_layout is not None:
            layout_usage.update(new_axis_layout)
            figure_overflow["layout"].update(new_axis_layout)
            return figure_overflow, figure_usage
    new_episode = make_episode(study_agent, scenario)
    figure_overflow["data"] = new_episode.total_overflow_trace
    maintenance_traces = EpisodeTrace.get_maintenance_trace(new_episode, ["total"])
    if len(maintenance_traces) != 0:
        maintenance_trace[0].update({"name": "Nb of maintenances"})
        figure_overflow["data"].append(maintenance_trace[0])

    figure_usage["data"] = new_episode.usage_rate_trace
    return figure_overflow, figure_usage


@app.callback(
    Output("action_timeserie", "figure"),
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("action_timeserie", "figure"),
     State("agent_ref", "data"),
     State("scenario", "data")]
)
def update_actions_graph(study_agent, relayout_data_store, figure, agent_ref, scenario):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    return make_action_ts(study_agent, agent_ref, scenario, figure['layout'])


@app.callback(
    [Output("inspector_datable", "columns"),
     Output("inspector_datable", "data")],
    [Input('agent_study', 'data'),
     Input("scenario", "data")]
)
def update_agent_log_action_table(study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    table = actions_model.get_action_table_data(new_episode)
    table['id'] = table['timestep']
    table.set_index('id', inplace=True, drop=False)
    return [{"name": i, "id": i} for i in table.columns if i != 'id'], table.to_dict("record")


@app.callback(
    [Output("distribution_substation_action_chart", "figure"),
     Output("distribution_line_action_chart", "figure")],
    [Input('agent_study', 'data')],
    [State("distribution_substation_action_chart", "figure"),
     State("distribution_line_action_chart", "figure"),
     State("scenario", "data")]
)
def update_agent_log_action_graphs(study_agent, figure_sub, figure_switch_line, scenario):
    new_episode = make_episode(study_agent, scenario)
    figure_sub["data"] = actions_model.get_action_per_sub(new_episode)
    figure_switch_line["data"] = actions_model.get_action_per_line(new_episode)
    return figure_sub, figure_switch_line


@app.callback(
    Output("tooltip_table", "children"),
    [Input("inspector_datable", "active_cell")],
    [State('agent_study', 'data'),
     State("scenario", "data"),
     State("inspector_datable", "data")]
)
def update_more_info(active_cell, study_agent, scenario, data):
    if active_cell is None:
        raise PreventUpdate
    new_episode = make_episode(study_agent, scenario)
    row_id = active_cell["row_id"]
    act = new_episode.actions[row_id]
    return str(act)
