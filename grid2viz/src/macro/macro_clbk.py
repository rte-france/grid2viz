"""
    This files handles the generic information about the agent of reference of the selected scenario
    and let choose and compute study agent information.
"""
import datetime as dt

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import numpy as np
import plotly.graph_objects as go

from grid2viz.src.manager import make_episode, make_network
from grid2viz.src.kpi import EpisodeTrace
from grid2viz.src.kpi import actions_model
from grid2viz.src.utils.graph_utils import (
    get_axis_relayout, relayout_callback, layout_def, layout_no_data, max_or_zero)
from grid2viz.src.kpi.maintenances import (hist_duration_maintenances)

from grid2viz.src.utils.common_graph import make_action_ts, make_rewards_ts


def register_callbacks_macro(app):
    @app.callback(
        [Output("rewards_timeserie", "figure"),
         Output("cumulated_rewards_timeserie", "figure"),],
        [Input('agent_study', 'data'),
         Input('relayoutStoreMacro', 'data')],
        [State("rewards_timeserie", "figure"),
         State("cumulated_rewards_timeserie", "figure"),
         State("agent_ref", "data"),
         State("scenario", "data"),
         State("agent_study", "modified_timestamp"),
         State("relayoutStoreMacro", "modified_timestamp")]
    )
    def load_reward_data_scatter(study_agent, relayout_data_store, rew_figure,
                                 cumrew_figure,
                                 ref_agent, scenario,
                                 agent_study_ts, relayoutStoreMacro_ts):
        """Compute and  create figure with instant and cumulated rewards of the study and ref agent"""
        rew_layout = rew_figure["layout"]
        cumrew_layout = cumrew_figure["layout"]
        if agent_study_ts is not None and relayoutStoreMacro_ts is not None:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"]
                         and relayoutStoreMacro_ts > agent_study_ts)
        else:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"])
        if condition:
            relayout_data = relayout_data_store["relayout_data"]
            rew_new_axis_layout = get_axis_relayout(rew_figure, relayout_data)
            cumrew_new_axis_layout = get_axis_relayout(cumrew_figure, relayout_data)
            if rew_new_axis_layout is not None or cumrew_new_axis_layout is not None:
                if rew_new_axis_layout is not None:
                    rew_layout.update(rew_new_axis_layout)
                if cumrew_new_axis_layout is not None:
                    cumrew_layout.update(cumrew_new_axis_layout)
                return rew_figure, cumrew_figure

        return make_rewards_ts(study_agent, ref_agent, scenario, rew_layout, cumrew_layout)

    @app.callback(
        Output("agent_study_pie_chart", "figure"),
        [Input('agent_study', 'data')],
        [State("agent_study_pie_chart", "figure"),
         State("scenario", "data")]
    )
    def update_action_repartition_pie(study_agent, figure, scenario):
        new_episode = make_episode(study_agent, scenario)
        figure['data'] = action_repartition_pie(new_episode)
        figure['layout'].update(
            actions_model.update_layout(
                figure["data"][0].values == (0, 0, 0),
                "No Actions for this Agent"))
        return figure


    def action_repartition_pie(agent):
        nb_actions = agent.action_data_table[
            ['action_line', 'action_subs', 'action_redisp']].sum()
        return [go.Pie(
            labels=["Actions on Lines", "Actions on Substations", "Redispatching Actions"],
            values=[nb_actions["action_line"], nb_actions["action_subs"], nb_actions["action_redisp"]]
        )]

    @app.callback(
        Output("network_actions", "figure"),
        [Input("agent_study", "data")],
        [State("scenario", "data")]
    )
    def update_network_graph(study_agent, scenario):
        episode = make_episode(study_agent, scenario)
        modified_lines = actions_model.get_modified_lines(episode)
        line_values = [None] * episode.n_lines
        for line in modified_lines.index:
            line_values[np.where(episode.line_names == line)[0][0]] = line
        network_graph = make_network(episode).plot_info(
            observation=episode.observations[0],
            line_values=line_values,
        )
        return network_graph


    @app.callback(
        Output("timeseries_table", "data"),
        [Input("rewards_timeserie", "clickData"),
         Input("agent_log_selector", "value")],
        [State("timeseries_table", "data"),
         State("agent_study", "data")]
    )
    def add_timestamp(click_data, new_agent, data, agent_stored):
        if new_agent != agent_stored or click_data is None:
            if data is not None:
                return data
            else:
                return []
        time_stamp_str = click_data["points"][0]["x"]
        try:
            dt.datetime.strptime(time_stamp_str, '%Y-%m-%d %H:%M')
        except ValueError:
            time_stamp_str = time_stamp_str + " 00:00"
        new_data = {"Timestamps": time_stamp_str}
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
         Input("rewards_timeserie", "relayoutData"),
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
        score = f'{get_score_agent(new_episode):,}'
        nb_overflow = f'{get_nb_overflow_agent(new_episode):,}'
        nb_action = f'{get_nb_action_agent(new_episode):,}'

        return score, nb_overflow, nb_action


    def get_score_agent(agent):
        score = agent.meta["cumulative_reward"]
        return round(score)


    def get_nb_overflow_agent(agent):
        return agent.total_overflow_ts["value"].sum()


    def get_nb_action_agent(agent):
        return int(agent.action_data_table[['action_line', 'action_subs']].sum(
            axis=1).sum())


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
         State("scenario", "data"),
         State("agent_study", "modified_timestamp"),
         State("relayoutStoreMacro", "modified_timestamp")]
    )
    def update_agent_log_graph(study_agent, relayout_data_store,
                               figure_overflow, figure_usage, scenario,
                               agent_study_ts, relayoutStoreMacro_ts):

        if agent_study_ts is not None and relayoutStoreMacro_ts is not None:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"]
                         and relayoutStoreMacro_ts > agent_study_ts)
        else:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"])
        if condition:
            relayout_data = relayout_data_store["relayout_data"]
            layout_usage = figure_usage["layout"]
            new_axis_layout = get_axis_relayout(figure_usage, relayout_data)
            if new_axis_layout is not None:
                layout_usage.update(new_axis_layout)
                figure_overflow["layout"].update(new_axis_layout)
                return figure_overflow, figure_usage
        new_episode = make_episode(study_agent, scenario)
        figure_overflow["data"] = new_episode.total_overflow_trace.copy()
        maintenance_traces = EpisodeTrace.get_maintenance_trace(new_episode, ["total"])
        if len(maintenance_traces) != 0:
            maintenance_traces[0].update({"name": "Nb of maintenances"})
            figure_overflow["data"].append(maintenance_traces[0])

        hazard_traces = EpisodeTrace.get_hazard_trace(new_episode, ["total"]).copy()
        if len(hazard_traces) != 0:
            hazard_traces[0].update({"name": "Nb of hazards"})
            figure_overflow["data"].append(hazard_traces[0])

        attacks_trace = EpisodeTrace.get_attacks_trace(new_episode).copy()
        if len(attacks_trace) != 0:
            attacks_trace[0].update({"name": "Attacks"})
            figure_overflow["data"].append(attacks_trace[0])

        figure_usage["data"] = new_episode.usage_rate_trace

        return figure_overflow, figure_usage


    @app.callback(
        Output("action_timeserie", "figure"),
        [Input('agent_study', 'data'),
         Input('relayoutStoreMacro', 'data')],
        [State("action_timeserie", "figure"),
         State("agent_ref", "data"),
         State("scenario", "data"),
         State("agent_study", "modified_timestamp"),
         State("relayoutStoreMacro", "modified_timestamp")]
    )
    def update_actions_graph(study_agent, relayout_data_store, figure,
                             agent_ref, scenario,
                             agent_study_ts, relayoutStoreMacro_ts):
        if agent_study_ts is not None and relayoutStoreMacro_ts is not None:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"]
                         and relayoutStoreMacro_ts > agent_study_ts)
        else:
            condition = (relayout_data_store is not None
                         and relayout_data_store["relayout_data"])
        if condition:
            relayout_data = relayout_data_store["relayout_data"]
            layout = figure["layout"]
            new_axis_layout = get_axis_relayout(figure, relayout_data)
            if new_axis_layout is not None:
                layout.update(new_axis_layout)
                return figure

        return make_action_ts(study_agent, agent_ref, scenario, figure['layout'])


    action_table_name_converter = dict(
        timestep="Timestep",
        timestamp="Timestamp",
        timestep_reward="Reward",
        action_line="Action on line",
        action_subs="Action on sub",
        action_redisp="Action of redispatch",
        redisp_impact="Redispatch impact",
        line_name="Line name",
        sub_name="Sub name",
        gen_name="Gen name",
        action_id="Action id",
        distance="Topological distance"
    )

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
        cols_to_exclude = ["id", "lines_modified", "subs_modified", "gens_modified"]
        cols = [{"name": action_table_name_converter[col], "id": col} for col in
                table.columns if col not in cols_to_exclude]
        return cols, table.to_dict("record")


    @app.callback(
        [Output("distribution_substation_action_chart", "figure"),
         Output("distribution_line_action_chart", "figure"),
         Output("distribution_redisp_action_chart", "figure")],
        [Input('agent_study', 'data')],
        [State("distribution_substation_action_chart", "figure"),
         State("distribution_line_action_chart", "figure"),
         State("distribution_redisp_action_chart", "figure"),
         State("scenario", "data"),
         State("agent_ref", "data")]
    )
    def update_agent_log_action_graphs(study_agent, figure_sub, figure_switch_line,
                                       figure_redisp, scenario, ref_agent):
        new_episode = make_episode(study_agent, scenario)
        ref_episode = make_episode(ref_agent, scenario)
        y_max = None
        figure_sub["data"] = actions_model.get_action_per_sub(new_episode)
        if len(figure_sub["data"][0]["x"]) != 0:
            figure_sub["data"].append(actions_model.get_action_per_sub(ref_episode)[0])
            y_max = max(map(max_or_zero, [trace.y for trace in figure_sub["data"]])) + 1
        figure_switch_line["data"] = actions_model.get_action_per_line(new_episode)
        if len(figure_switch_line["data"][0]["x"]) != 0:
            figure_switch_line["data"].append(actions_model.get_action_per_line(ref_episode)[0])
            if y_max is None:
                y_max = max(map(max_or_zero, [trace.y for trace in figure_switch_line["data"]])) + 1
            if max(map(max_or_zero, [trace.y for trace in figure_switch_line["data"]])) > y_max:
                y_max = max(map(max_or_zero, [trace.y for trace in figure_switch_line["data"]])) + 1
        figure_redisp["data"] = actions_model.get_action_redispatch(new_episode)
        if len(figure_redisp["data"][0]["x"]) != 0:
            figure_redisp["data"].append(actions_model.get_action_redispatch(ref_episode)[0])
            if y_max is None:
                y_max = max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]])) + 1
            if max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]])) > y_max:
                y_max = max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]])) + 1

        figure_sub["layout"].update(
            actions_model.update_layout(
                len(figure_sub["data"][0]["x"]) == 0,
                "No Actions on subs for this Agent"))
        figure_switch_line["layout"].update(
            actions_model.update_layout(
                len(figure_switch_line["data"][0]["x"]) == 0,
                "No Actions on lines for this Agent"))
        figure_redisp["layout"].update(
            actions_model.update_layout(
                len(figure_redisp["data"][0]["x"]) == 0,
                "No redispatching actions for this Agent"))

        if y_max:
            figure_sub["layout"]["yaxis"].update(range=[0, y_max])
            figure_switch_line["layout"]["yaxis"].update(range=[0, y_max])
            figure_redisp["layout"]["yaxis"].update(range=[0, y_max])

        return figure_sub, figure_switch_line, figure_redisp


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
