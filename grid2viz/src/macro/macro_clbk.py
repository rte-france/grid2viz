# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

"""
    This files handles the generic information about the agent of reference of the selected scenario
    and let choose and compute study agent information.
"""
import datetime as dt
from operator import itemgetter

import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pathlib import Path

from grid2viz.src.kpi import EpisodeTrace
from grid2viz.src.kpi import actions_model
from grid2viz.src.manager import (
    make_episode,
    grid2viz_home_directory,
    make_network_agent_overview,
)
from grid2viz.src.utils.callbacks_helpers import toggle_modal_helper
from grid2viz.src.utils.common_graph import make_action_ts, make_rewards_ts
from grid2viz.src.utils.constants import DONT_SHOW_FILENAME
from grid2viz.src.utils.graph_utils import (
    get_axis_relayout,
    relayout_callback,
    max_or_zero,
)


def register_callbacks_macro(app):

    # Synchronized graphs
    @app.callback(
        [
            Output("rewards_timeserie", "figure"),
            Output("cumulated_rewards_timeserie", "figure"),
            Output("overflow_graph_study", "figure"),
            Output("usage_rate_graph_study", "figure"),
            Output("action_timeserie", "figure"),
        ],
        [
            Input("agent_study", "modified_timestamp"),
            Input("agent_ref", "data"),
            Input("relayoutStoreMacro", "data"),
        ],
        [
            State("rewards_timeserie", "figure"),
            State("cumulated_rewards_timeserie", "figure"),
            State("overflow_graph_study", "figure"),
            State("usage_rate_graph_study", "figure"),
            State("action_timeserie", "figure"),
            State("scenario", "data"),
            State("agent_study", "data"),
            State("relayoutStoreMacro", "modified_timestamp"),
        ],
    )
    def update_synchronized_figures(
        agent_study_ts,
        ref_agent,
        relayout_data_store,
        rew_figure,
        cumrew_figure,
        overflow_figure,
        usage_rate_figure,
        actions_figure,
        scenario,
        study_agent,
        relayoutStoreMacro_ts,
    ):

        figures = [
            rew_figure,
            cumrew_figure,
            overflow_figure,
            usage_rate_figure,
            actions_figure,
        ]

        episode = make_episode(study_agent, scenario)

        if agent_study_ts is not None and relayoutStoreMacro_ts is not None:
            condition = (
                relayout_data_store is not None
                and relayout_data_store["relayout_data"]
                and relayoutStoreMacro_ts > agent_study_ts
            )
        else:
            condition = (
                relayout_data_store is not None and relayout_data_store["relayout_data"]
            )
        if condition:
            relayout_data = relayout_data_store["relayout_data"]
            relayouted = False
            for figure in figures:
                axis_layout = get_axis_relayout(figure, relayout_data)
                if axis_layout is not None:
                    figure["layout"].update(axis_layout)
                    relayouted = True
            if relayouted:
                return figures
        new_reward_fig, new_cumreward_fig = make_rewards_ts(
            study_agent, ref_agent, scenario, rew_figure, cumrew_figure
        )

        overflow_figure["data"] = episode.total_overflow_trace.copy()
        for event in ["maintenance", "hazard", "attacks"]:
            func = getattr(EpisodeTrace, f"get_{event}_trace")
            traces = func(episode, ["total"])
            if len(traces) > 0:
                traces[0].update({"name": event.capitalize()})
                overflow_figure["data"].append(traces[0])

        usage_rate_figure["data"] = episode.usage_rate_trace

        new_action_fig = make_action_ts(
            study_agent, ref_agent, scenario, actions_figure["layout"]
        )

        return (
            new_reward_fig,
            new_cumreward_fig,
            overflow_figure,
            usage_rate_figure,
            new_action_fig,
        )

    @app.callback(
        Output("agent_study_pie_chart", "figure"),
        [Input("agent_study", "data")],
        [State("agent_study_pie_chart", "figure"), State("scenario", "data")],
    )
    def update_action_repartition_pie(study_agent, figure, scenario):
        new_episode = make_episode(study_agent, scenario)
        figure["data"] = action_repartition_pie(new_episode)
        figure["layout"].update(
            actions_model.update_layout(
                figure["data"][0].values == (0, 0, 0), "No Actions for this Agent"
            )
        )
        return figure

    def action_repartition_pie(agent):
        nb_actions = agent.action_data_table[
            ["action_line", "action_subs", "action_redisp"]
        ].sum()
        return [
            go.Pie(
                labels=[
                    "Actions on Lines",
                    "Actions on Substations",
                    "Redispatching Actions",
                ],
                values=[
                    nb_actions["action_line"],
                    nb_actions["action_subs"],
                    nb_actions["action_redisp"],
                ],
            )
        ]

    @app.callback(
        Output("network_actions", "figure"),
        [Input("agent_study", "data")],
        [State("scenario", "data")],
    )
    def update_network_graph(study_agent, scenario):
        episode = make_episode(study_agent, scenario)

        return make_network_agent_overview(episode)

    @app.callback(
        Output("timeseries_table", "data"),
        [Input("rewards_timeserie", "clickData"), Input("select_study_agent", "value")],
        [State("timeseries_table", "data"), State("agent_study", "data")],
    )
    def add_timestamp(click_data, new_agent, data, agent_stored):
        if new_agent != agent_stored:
            return []
        if click_data is None:
            if data is not None:
                return data
            else:
                return []
        time_stamp_str = click_data["points"][0]["x"]
        try:
            dt.datetime.strptime(time_stamp_str, "%Y-%m-%d %H:%M")
        except ValueError:
            time_stamp_str = time_stamp_str + " 00:00"
        new_data = {"Timestamps": time_stamp_str}
        if new_data not in data:
            data.append(new_data)
        return sorted(data, key=itemgetter("Timestamps"))

    @app.callback(
        Output("user_timestamps_store", "data"), [Input("timeseries_table", "data")]
    )
    def update_user_timestamps_store(timestamps):
        if timestamps is None:
            raise PreventUpdate
        return [
            dict(label=timestamp["Timestamps"], value=timestamp["Timestamps"])
            for timestamp in timestamps
        ]

    @app.callback(
        Output("relayoutStoreMacro", "data"),
        [
            Input("usage_rate_graph_study", "relayoutData"),
            Input("action_timeserie", "relayoutData"),
            Input("overflow_graph_study", "relayoutData"),
            Input("rewards_timeserie", "relayoutData"),
            Input("cumulated_rewards_timeserie", "relayoutData"),
        ],
        [State("relayoutStoreMacro", "data")],
    )
    def relayout_store(*args):
        return relayout_callback(*args)

    @app.callback(
        [
            Output("indicator_score_output", "children"),
            Output("indicator_survival_time", "children"),
            Output("indicator_nb_overflow", "children"),
            Output("indicator_nb_action", "children"),
            Output("indicator_nb_maintenances", "children"),
        ],
        [Input("agent_study", "data"), Input("scenario", "data")],
    )
    def update_nbs(study_agent, scenario):
        new_episode = make_episode(study_agent, scenario)
        score = f"{get_score_agent(new_episode):,}"
        survival_time = (
            f"{get_agent_survival_time(new_episode)}/{get_episode_length(new_episode)}"
        )
        nb_overflow = f"{get_nb_overflow_agent(new_episode):,}"
        nb_action = f"{get_nb_action_agent(new_episode):,}"
        nb_maintenances = f"{get_nb_maintenances(new_episode)}"

        return score, survival_time, nb_overflow, nb_action, nb_maintenances

    def get_score_agent(episode):
        score = episode.meta["cumulative_reward"]
        return round(score)

    def get_agent_survival_time(episode):
        return episode.meta["nb_timestep_played"]

    def get_episode_length(episode):
        return episode.meta["chronics_max_timestep"]

    def get_nb_overflow_agent(episode):
        return episode.total_overflow_ts["value"].sum()

    def get_nb_action_agent(episode):
        return int(
            episode.action_data_table[["action_line", "action_subs"]].sum(axis=1).sum()
        )

    def get_nb_maintenances(episode):
        return int(episode.nb_maintenances)

    # @app.callback(
    #     Output("agent_study", "data"),
    #     [Input('agent_log_selector', 'value')],
    #     [State("agent_study", "data"),
    #      State("scenario", "data")],
    # )
    # def update_study_agent(study_agent, stored_agent, scenario):
    #     if study_agent == stored_agent:
    #         raise PreventUpdate
    #     make_episode(study_agent, scenario)
    #     return study_agent

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
        distance="Topological distance",
        is_alarm="is_alarm",
        alarm_zone="alarm_zone"
    )

    @app.callback(
        [Output("inspector_datable", "columns"), Output("inspector_datable", "data")],
        [Input("agent_study", "data"), Input("scenario", "data")],
    )
    def update_agent_log_action_table(study_agent, scenario):
        new_episode = make_episode(study_agent, scenario)
        table = actions_model.get_action_table_data(new_episode)
        table["id"] = table["timestep"]
        table.set_index("id", inplace=True, drop=False)
        cols_to_exclude = ["id", "lines_modified", "subs_modified", "gens_modified","is_action"]
        cols = [
            {"name": action_table_name_converter[col], "id": col}
            for col in table.columns
            if col not in cols_to_exclude
        ]
        return cols, table.to_dict("record")

    @app.callback(
        [
            Output("distribution_substation_action_chart", "figure"),
            Output("distribution_line_action_chart", "figure"),
            Output("distribution_redisp_action_chart", "figure"),
        ],
        [Input("agent_study", "data"), Input("agent_ref", "data")],
        [
            State("distribution_substation_action_chart", "figure"),
            State("distribution_line_action_chart", "figure"),
            State("distribution_redisp_action_chart", "figure"),
            State("scenario", "data"),
        ],
    )
    def update_agent_log_action_graphs(
        study_agent, ref_agent, figure_sub, figure_switch_line, figure_redisp, scenario
    ):
        new_episode = make_episode(study_agent, scenario)
        ref_episode = make_episode(ref_agent, scenario)
        y_max = None
        figure_sub["data"] = actions_model.get_action_per_sub(new_episode)
        if len(figure_sub["data"][0]["x"]) != 0:
            figure_sub["data"].append(actions_model.get_action_per_sub(ref_episode)[0])
            y_max = max(map(max_or_zero, [trace.y for trace in figure_sub["data"]])) + 1
        figure_switch_line["data"] = actions_model.get_action_per_line(new_episode)
        if len(figure_switch_line["data"][0]["x"]) != 0:
            figure_switch_line["data"].append(
                actions_model.get_action_per_line(ref_episode)[0]
            )
            if y_max is None:
                y_max = (
                    max(
                        map(
                            max_or_zero,
                            [trace.y for trace in figure_switch_line["data"]],
                        )
                    )
                    + 1
                )
            if (
                max(map(max_or_zero, [trace.y for trace in figure_switch_line["data"]]))
                > y_max
            ):
                y_max = (
                    max(
                        map(
                            max_or_zero,
                            [trace.y for trace in figure_switch_line["data"]],
                        )
                    )
                    + 1
                )
        figure_redisp["data"] = actions_model.get_action_redispatch(new_episode)
        if len(figure_redisp["data"][0]["x"]) != 0:
            figure_redisp["data"].append(
                actions_model.get_action_redispatch(ref_episode)[0]
            )
            if y_max is None:
                y_max = (
                    max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]]))
                    + 1
                )
            if (
                max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]]))
                > y_max
            ):
                y_max = (
                    max(map(max_or_zero, [trace.y for trace in figure_redisp["data"]]))
                    + 1
                )

        figure_sub["layout"].update(
            actions_model.update_layout(
                len(figure_sub["data"][0]["x"]) == 0,
                "No Actions on subs for this Agent",
            )
        )
        figure_switch_line["layout"].update(
            actions_model.update_layout(
                len(figure_switch_line["data"][0]["x"]) == 0,
                "No Actions on lines for this Agent",
            )
        )
        figure_redisp["layout"].update(
            actions_model.update_layout(
                len(figure_redisp["data"][0]["x"]) == 0,
                "No redispatching actions for this Agent",
            )
        )

        if y_max:
            figure_sub["layout"]["yaxis"].update(range=[0, y_max])
            figure_switch_line["layout"]["yaxis"].update(range=[0, y_max])
            figure_redisp["layout"]["yaxis"].update(range=[0, y_max])

        return figure_sub, figure_switch_line, figure_redisp

    @app.callback(
        Output("tooltip_table", "children"),
        [Input("inspector_datable", "active_cell")],
        [
            State("agent_study", "data"),
            State("scenario", "data"),
            State("inspector_datable", "data"),
        ],
    )
    def update_more_info(active_cell, study_agent, scenario, data):
        if active_cell is None:
            raise PreventUpdate
        new_episode = make_episode(study_agent, scenario)
        row_id = active_cell["row_id"]
        act = new_episode.actions[row_id]
        return str(act)

    @app.callback(
        [
            Output("modal_macro", "is_open"),
            Output("dont_show_again_div_macro", "className"),
        ],
        [Input("close_macro", "n_clicks"), Input("page_help", "n_clicks")],
        [State("modal_macro", "is_open"), State("dont_show_again_macro", "checked")],
    )
    def toggle_modal(close_n_clicks, open_n_clicks, is_open, dont_show_again):
        dsa_filepath = Path(grid2viz_home_directory) / DONT_SHOW_FILENAME("macro")
        return toggle_modal_helper(
            close_n_clicks,
            open_n_clicks,
            is_open,
            dont_show_again,
            dsa_filepath,
            "page_help",
        )

    @app.callback(Output("modal_image_macro", "src"), [Input("url", "pathname")])
    def show_image(pathname):
        return app.get_asset_url("screenshots/agent_overview.png")
