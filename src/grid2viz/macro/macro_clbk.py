from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.app import app
from grid2kpi.episode.actions_model import get_actions_sum
from ..manager import make_episode, agents
from grid2kpi.episode import observation_model, EpisodeTrace
from grid2kpi.episode import actions_model
from src.grid2viz.utils.graph_utils import get_axis_relayout, RelayoutX, relayout_callback
from grid2kpi.episode.maintenances import (hist_duration_maintenances)
from src.grid2viz.utils.common_controllers import action_tooltip
from src.grid2viz.utils.perf_analyser import timeit


@app.callback(
    Output("cumulated_rewards_timeserie", "figure"),
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("cumulated_rewards_timeserie", "figure"),
     State("agent_ref", "data"),
     State("scenario", "data")]
)
def load_reward_data_scatter(study_agent, relayout_data_store, figure, ref_agent, scenario):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    new_episode = make_episode(study_agent, scenario)
    ref_episode = make_episode(ref_agent, scenario)
    actions_ts = new_episode.action_data_table.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    df = observation_model.get_df_computed_reward(new_episode)
    action_events_df = pd.DataFrame(
        index=df["timestep"], data=np.nan, columns=["action_events"])
    action_events_df.loc[(actions_ts["Nb Actions"] > 0).values, "action_events"] = \
        df.loc[(actions_ts["Nb Actions"] > 0).values, "rewards"].values
    action_trace = go.Scatter(
        x=action_events_df.index, y=action_events_df["action_events"], name="Actions",
        mode='markers', marker_color='#FFEB3B',
        marker={"symbol": "hexagon", "size": 10}
    )
    ref_episode_reward_trace = ref_episode.reward_trace
    studied_agent_reward_trace = new_episode.reward_trace

    figure['data'] = [*ref_episode_reward_trace, *studied_agent_reward_trace,
                      action_trace]
    figure['layout'] = {**figure['layout'],
                        'yaxis': {'title': 'Instant Reward'},
                        'yaxis2': {'title': 'Cumulated Reward', 'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }
    return figure


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
def add_timestamp(clickData, new_agent, data, agent_stored):
    if new_agent != agent_stored:
        return []
    if data is None:
        data = []
    new_data = {"Timestamps": clickData["points"][0]["x"]}
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
    maintenance_trace = EpisodeTrace.get_maintenance_trace(new_episode, ["total"])[0]
    maintenance_trace.update({"name": "Nb of maintenances"})
    figure_overflow["data"].append(maintenance_trace)
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

    new_episode = make_episode(study_agent, scenario)
    actions_ts = get_actions_sum(new_episode)
    ref_episode = make_episode(agent_ref, scenario)
    ref_agent_actions_ts = get_actions_sum(ref_episode)
    figure["data"] = [
        go.Scatter(x=new_episode.action_data_table.timestamp,
                   y=actions_ts["Nb Actions"], name=study_agent,
                   text=action_tooltip(new_episode.actions)),
        go.Scatter(x=ref_episode.action_data_table.timestamp,
                   y=ref_agent_actions_ts["Nb Actions"], name=agent_ref,
                   text=action_tooltip(ref_episode.actions)),

        go.Scatter(x=new_episode.action_data_table.timestamp,
                   y=new_episode.action_data_table["distance"], name=study_agent + " distance", yaxis='y2'),
        go.Scatter(x=ref_episode.action_data_table.timestamp,
                   y=ref_episode.action_data_table["distance"], name=agent_ref + " distance", yaxis='y2'),
    ]
    figure['layout'] = {**figure['layout'],
                        'yaxis': {'title': 'Actions'},
                        'yaxis2': {'title': 'Distance','side': 'right', 'anchor': 'x', 'overlaying': 'y'}}
    return figure


@app.callback(
    [Output("inspector_datable", "columns"),
     Output("inspector_datable", "data")],
    [Input('agent_study', 'data'),
     Input("scenario", "data")]
)
def update_agent_log_action_table(study_agent, scenario):
    new_episode = make_episode(study_agent, scenario)
    table = actions_model.get_action_table_data(new_episode)
    return [{"name": i, "id": i} for i in table.columns], table.to_dict("record")


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
    [Input('agent_study', 'data'),
     Input("inspector_datable", "active_cell"),
     Input("scenario", "data")]
)
def update_more_info(study_agent, active_cell, scenario):
    if active_cell is None:
        raise PreventUpdate
    row = active_cell["row"]
    new_episode = make_episode(study_agent, scenario)
    act = new_episode.actions[row]
    return str(act)
