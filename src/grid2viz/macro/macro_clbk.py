from collections import Counter

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from src.app import app
from src.grid2kpi.manager import episode, make_episode, base_dir, indx, agent_ref
from src.grid2kpi.episode import observation_model
from src.grid2kpi.episode import actions_model
from src.grid2viz.utils.graph_utils import get_axis_relayout, RelayoutX, relayout_callback
from src.grid2kpi.episode.maintenances import (
    nb_maintenances, duration_maintenances, hist_duration_maintenances)


# TODO add contant color code for ref and studied agent
# studied_color = {'primary': #color, 'secondary': #color}
# ref_color = {'primary': #color, 'secondary': #color}

@app.callback(
    Output("cumulated_rewards_timeserie", "figure"),
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("cumulated_rewards_timeserie", "figure")]
)
def load_reward_data_scatter(study_agent, relayout_data_store, figure):

    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    ref_episode_reward_trace = observation_model.get_ref_agent_rewards_trace(
        episode)
    studied_agent_reward_trace = observation_model.get_studied_agent_reward_trace(
        make_episode(base_dir, study_agent, indx))

    figure['data'] = [*ref_episode_reward_trace, *studied_agent_reward_trace]
    figure['layout'] = {**figure['layout'],
                        'yaxis2': {'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }
    return figure


@app.callback(
    Output("agent_study_pie_chart", "figure"),
    [Input('agent_study', 'data')],
    [State("agent_study_pie_chart", "figure")]
)
def load_pie_chart(study_agent, figure):
    new_episode = make_episode(base_dir, study_agent, indx)
    nb_actions = new_episode.action_data[['action_line', 'action_subs']].sum()
    figure['data'] = [go.Pie(
        labels=["Actions on Lines", "Actions on Substations"],
        values=[nb_actions["action_line"], nb_actions["action_subs"]]
    )]
    return figure


@app.callback(
    Output("maintenance_duration", "figure"),
    [Input('agent_study', 'data')],
    [State("maintenance_duration", "figure")]
)
def maintenance_duration_hist(study_agent, figure):
    new_episode = make_episode(base_dir, study_agent, indx)
    figure['data'] = [go.Histogram(
        x=hist_duration_maintenances(new_episode)
    )]
    return figure


@app.callback(
    Output("timeseries_table", "data"),
    [Input("cumulated_rewards_timeserie", "clickData")],
    [State("timeseries_table", "data")]
)
def add_timestamp(clickData, data):
    if data is None:
        data = []
    new_data = {"Timestamps": clickData["points"][0]["x"]}
    if new_data not in data:
        data.append(new_data)
    return data


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
    [Input('agent_study', 'data')]
)
def update_nbs(study_agent):
    new_episode = make_episode(base_dir, study_agent, indx)
    score = new_episode.meta["cumulative_reward"]
    nb_overflow = new_episode.total_overflow_ts["value"].sum()
    nb_action = new_episode.action_data[['action_line', 'action_subs']].sum(
        axis=1).sum()
    return round(score), nb_overflow, nb_action


@app.callback(
    Output("agent_study", "data"),
    [Input('agent_log_selector', 'value')],
)
def update_study_agent(study_agent):
    make_episode(base_dir, study_agent, indx)
    return study_agent


@app.callback(
    [Output("overflow_graph_study", "figure"), Output(
        "usage_rate_graph_study", "figure")],
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("overflow_graph_study", "figure"),
     State("usage_rate_graph_study", "figure")]
)
def update_agent_log_graph(study_agent, relayout_data_store, figure_overflow, figure_usage):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout_usage = figure_usage["layout"]
        new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
        if new_axis_layout is not None:
            layout_usage.update(new_axis_layout)
            figure_overflow["layout"].update(new_axis_layout)
            return figure_overflow, figure_usage
    new_episode = make_episode(base_dir, study_agent, indx)
    figure_overflow["data"] = observation_model.get_total_overflow_trace(
        new_episode)
    figure_usage["data"] = observation_model.get_usage_rate_trace(new_episode)
    return figure_overflow, figure_usage


@app.callback(
    Output("action_timeserie", "figure"),
    [Input('agent_study', 'data'),
     Input('relayoutStoreMacro', 'data')],
    [State("action_timeserie", "figure")]
)
def update_actions_graph(study_agent, relayout_data_store, figure):
    if relayout_data_store is not None and relayout_data_store["relayout_data"]:
        relayout_data = relayout_data_store["relayout_data"]
        layout = figure["layout"]
        new_axis_layout = get_axis_relayout(figure, relayout_data)
        if new_axis_layout is not None:
            layout.update(new_axis_layout)
            return figure

    new_episode = make_episode(base_dir, study_agent, indx)
    actions_ts = new_episode.action_data.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    ref_episode = make_episode(base_dir, agent_ref, indx)
    ref_agent_actions_ts = ref_episode.action_data.set_index("timestamp")[[
        'action_line', 'action_subs'
    ]].sum(axis=1).to_frame(name="Nb Actions")
    figure["data"] = [
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=actions_ts["Nb Actions"], name=study_agent,
                   text=action_tooltip(new_episode.actions)),
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=ref_agent_actions_ts["Nb Actions"], name=agent_ref,
                   text=action_tooltip(ref_episode.actions)),

        go.Scatter(x=new_episode.action_data.timestamp,
                   y=new_episode.action_data["distance"], name=study_agent + " distance", yaxis='y2'),
        go.Scatter(x=new_episode.action_data.timestamp,
                   y=ref_episode.action_data["distance"], name=agent_ref + " distance", yaxis='y2'),
    ]
    figure['layout'] = {**figure['layout'],
                        'yaxis2': {'side': 'right', 'anchor': 'x', 'overlaying': 'y'}, }
    return figure


def action_tooltip(episode_actions):
    tooltip = []
    actions_impact = [action.impact_on_objects() for action in episode_actions]

    for action in actions_impact:
        impact_detail = []
        if action['has_impact']:
            injection = action['injection']
            force_line = action['force_line']
            switch_line = action['switch_line']
            topology = action['topology']

            if injection['changed']:
                for detail in injection['impacted']:
                    impact_detail.append(" injection set {} to {} <br>"
                                         .format(detail['set'], detail['to']))

            if force_line['changed']:
                reconnections = force_line['reconnections']
                disconnections = force_line['disconnections']

                if reconnections['count'] > 0:
                    impact_detail.append(" force reconnection of {} powerlines ({}) <br>"
                                         .format(reconnections['count'], reconnections['powerlines']))

                if disconnections['count'] > 0:
                    impact_detail.append(" force disconnection of {} powerlines ({}) <br>"
                                         .format(disconnections['count'], disconnections['powerlines']))

            if switch_line['changed']:
                impact_detail.append(" switch status of {} powerlines ({}) <br>"
                                     .format(switch_line['count'], switch_line['powerlines']))

            if topology['changed']:
                bus_switch = topology['bus_switch']
                assigned_bus = topology['assigned_bus']
                disconnected_bus = topology['disconnect_bus']

                if len(bus_switch) > 0:
                    for switch in bus_switch:
                        impact_detail.append(" switch bus of {} {} on substation {} <br>"
                                             .format(switch['object_type'], switch['object_id'],
                                                     switch['substation']))
                if len(assigned_bus) > 0:
                    for assignment in assigned_bus:
                        impact_detail.append(" assign bus {} to {} {} on substation {} <br>"
                                             .format(assignment['bus'], assignment['object_type'],
                                                     assignment['object_id'], assignment['substation']))
                if len(disconnected_bus) > 0:
                    for disconnection in disconnected_bus:
                        impact_detail.append(" disconnect bus {} {} on substation {} <br>"
                                             .format(disconnection['object_type'], disconnection['object_id'],
                                                     disconnection['substation']))
            tooltip.append(''.join(impact_detail))
        else:
            tooltip.append('Do nothing')

    return tooltip


@app.callback(
    [Output("inspector_datable", "columns"),
     Output("inspector_datable", "data")],
    [Input('agent_study', 'data')],
    [State("inspector_datable", "data")]
)
def update_agent_log_action_table(study_agent, data):
    new_episode = make_episode(base_dir, study_agent, indx)
    table = actions_model.get_action_table_data(new_episode)
    return [{"name": i, "id": i} for i in table.columns], table.to_dict("record")


@app.callback(
    [Output("distribution_substation_action_chart", "figure"),
     Output("distribution_line_action_chart", "figure")],
    [Input('agent_study', 'data')],
    [State("distribution_substation_action_chart", "figure"),
     State("distribution_line_action_chart", "figure")]
)
def update_agent_log_action_graphs(study_agent, figure_sub, figure_switch_line):
    new_episode = make_episode(base_dir, study_agent, indx)
    figure_sub["data"] = actions_model.get_action_per_sub(new_episode)
    # figure_line["data"] = actions_model.get_action_set_line_trace(new_episode)
    # figure_bus["data"] = actions_model.get_action_change_bus_trace(new_episode)
    figure_switch_line["data"] = actions_model.get_action_switch_line_trace(
        new_episode)
    return figure_sub, figure_switch_line
