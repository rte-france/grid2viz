"""
    Utility functions for creation of graph and graph component used several times.
"""

import numpy as np
import pandas as pd
from plotly import graph_objects as go

from grid2viz.src.kpi import EpisodeTrace, observation_model
from grid2viz.src.kpi.actions_model import get_actions_sum
from grid2viz.src.manager import make_episode


def ts_graph_avail_assets(ts_kind, episode):
    """
    Get a list of available assets for a selected kind of timeserie of an episode.

    This method is used with the followed kind of timeseries:
        - Hazards
        - Maintenances
        - Production
        - Load

    .. warning:: By default if no kind is given the load's assets will be returned

    :param ts_kind: kind of timeseries wanted
    :param episode: episode studied
    :param prod_types: The different types of production
    :return: list of of available asset in form of tuple (option, value)
    """
    if ts_kind in ["Hazards", "Maintenances"]:
        options, value = [
            {"label": line_name, "value": line_name}
            for line_name in ["total", *episode.line_names]
        ], "total"  # episode.line_names[0]
    elif ts_kind == "Production":
        prod_types = episode.get_prod_types()
        options = [
            {"label": prod_name, "value": prod_name}
            for prod_name in [
                *list(set(prod_types.values())),
                "total",
                *episode.prod_names,
            ]
        ]
        value = "solar"  # episode.prod_names[0]
    else:
        options = [
            {"label": load_name, "value": load_name}
            for load_name in ["total", "total_intercos", *episode.load_names]
        ]
        value = "total"  # episode.load_names[0]

    return options, value


def environment_ts_data(kind, episode, equipments):
    """
    Get the selected kind of timeserie trace for an equipment used in episode.

    There's four kind of trace possible:
        - Load
        - Production
        - Hazards
        - Maintenances

    :param kind: Type of trace
    :param episode: Episode studied
    :param equipments: A equipment to analyze like substation etc.
    :param prod_types: Different types of production
    :return: A list of plotly object corresponding to a trace
    """
    if kind == "Load":
        return EpisodeTrace.get_load_trace_per_equipment(episode, equipments)
    if kind == "Production":
        prod_types = episode.get_prod_types()
        return EpisodeTrace.get_all_prod_trace(episode, prod_types, equipments)
    if kind == "Hazards":
        return EpisodeTrace.get_hazard_trace(episode, equipments)
    if kind == "Maintenances":
        return EpisodeTrace.get_maintenance_trace(episode, equipments)


def agent_overflow_usage_rate_trace(episode, figure_overflow, figure_usage):
    """
    Get the trace of the overflow and the usage_rate for given episode.

    :param episode: Episode studied
    :param figure_overflow: figure which will contain the overflow trace
    :param figure_usage: figure which will contain the usage rate trace
    :returns: Plotly figure for usage_rate and for overflow
    """
    figure_overflow["data"] = episode.total_overflow_trace
    figure_usage["data"] = episode.usage_rate_trace
    return figure_overflow, figure_usage


def action_tooltip(episode_actions):
    """
    This is used to get a detailed impact action in tooltip format in order to display this tooltip on a
    plotly graph.

    :param episode_actions: episode's actions for the inspected scenario
    :return: string with action's details
    """
    tooltip = []
    # avoid reevaluation of append() see: https://wiki.python.org/moin/PythonSpeed/PerformanceTips
    tooltip_append = tooltip.append
    actions_impact = [action.impact_on_objects() for action in episode_actions]

    for action in actions_impact:
        impact_detail = []
        impact_append = impact_detail.append

        if action["has_impact"]:
            injection = action["injection"]
            force_line = action["force_line"]
            switch_line = action["switch_line"]
            topology = action["topology"]
            redispatch = action["redispatch"]

            if injection["changed"]:
                [
                    impact_append(
                        " Injection set {} to {} <br>".format(
                            detail["set"], detail["to"]
                        )
                    )
                    for detail in injection["impacted"]
                ]

            if force_line["changed"]:
                reconnections = force_line["reconnections"]
                disconnections = force_line["disconnections"]

                if reconnections["count"] > 0:
                    impact_append(
                        " Force reconnection of {} powerlines ({}) <br>".format(
                            reconnections["count"], reconnections["powerlines"]
                        )
                    )

                if disconnections["count"] > 0:
                    impact_append(
                        " Force disconnection of {} powerlines ({}) <br>".format(
                            disconnections["count"], disconnections["powerlines"]
                        )
                    )

            if switch_line["changed"]:
                impact_append(
                    " Switch status of {} powerlines ({}) <br>".format(
                        switch_line["count"], switch_line["powerlines"]
                    )
                )

            if topology["changed"]:
                bus_switch = topology["bus_switch"]
                assigned_bus = topology["assigned_bus"]
                disconnected_bus = topology["disconnect_bus"]

                if len(bus_switch) > 0:
                    [
                        impact_append(
                            " Switch bus of {} {} on substation {} <br>".format(
                                switch["object_type"],
                                switch["object_id"],
                                switch["substation"],
                            )
                        )
                        for switch in bus_switch
                    ]

                if len(assigned_bus) > 0:
                    [
                        impact_append(
                            " Assign bus {} to {} {} on substation {} <br>".format(
                                assignment["bus"],
                                assignment["object_type"],
                                assignment["object_id"],
                                assignment["substation"],
                            )
                        )
                        for assignment in assigned_bus
                    ]

                if len(disconnected_bus) > 0:
                    [
                        impact_append(
                            " Disconnect bus {} {} on substation {} <br>".format(
                                disconnection["object_type"],
                                disconnection["object_id"],
                                disconnection["substation"],
                            )
                        )
                        for disconnection in disconnected_bus
                    ]

            if redispatch["changed"]:
                generators = redispatch["generators"]
                for gen_dict in generators:
                    gen_name = gen_dict["gen_name"]
                    r_amount = gen_dict["amount"]
                    impact_append("Redispatch {} of {} <br>".format(gen_name, r_amount))

            tooltip_append("".join(impact_detail))
        else:
            tooltip_append("Do nothing")

    return tooltip


def make_action_ts(study_agent, ref_agent, scenario, layout_def=None):
    """
    Make the action timeseries trace of study and reference agents.

    :param study_agent: studied agent to compare
    :param ref_agent: reference agent to compare with
    :param scenario:
    :param layout_def: layout page
    :return: nb action and distance for each agents
    """
    ref_episode = make_episode(ref_agent, scenario)
    study_episode = make_episode(study_agent, scenario)
    actions_ts = get_actions_sum(study_episode)
    ref_agent_actions_ts = get_actions_sum(ref_episode)

    # used below to make sure the x-axis length is the study agent one
    study_agent_length = len(study_episode.action_data_table)

    action_events_df = pd.DataFrame(
        index=actions_ts.index, data=np.nan, columns=["action_events"]
    )
    action_events_df.loc[
        (actions_ts["Nb Actions"] > 0).values, "action_events"
    ] = study_episode.action_data_table.loc[
        (actions_ts["Nb Actions"] > 0).values, "distance"
    ].values
    study_text = ["<br>-".join(str(act).split("-")) for act in study_episode.actions]
    action_trace = go.Scatter(
        x=action_events_df.index,
        y=action_events_df["action_events"],
        name=study_agent + " Actions",
        mode="markers",
        marker_color="#FFEB3B",
        marker={"symbol": "hexagon", "size": 10},
        text=study_text,
    )

    ref_action_events_df = pd.DataFrame(
        index=ref_agent_actions_ts.index, data=np.nan, columns=["action_events"]
    )
    ref_action_events_df.loc[
        (ref_agent_actions_ts["Nb Actions"] > 0).values, "action_events"
    ] = ref_episode.action_data_table.loc[
        (ref_agent_actions_ts["Nb Actions"] > 0).values, "distance"
    ].values

    ref_text = ["<br>-".join(str(act).split("-")) for act in ref_episode.actions]
    ref_text = ref_text[:study_agent_length]
    ref_action_trace = go.Scatter(
        x=ref_action_events_df.index[:study_agent_length],
        y=ref_action_events_df["action_events"][:study_agent_length],
        name=ref_agent + " Actions",
        mode="markers",
        marker_color="#FF5000",
        marker={"symbol": "hexagon", "size": 10},
        text=ref_text,
    )

    distance_trace = go.Scatter(
        x=study_episode.action_data_table.timestamp,
        y=study_episode.action_data_table["distance"],
        name=study_agent,
    )

    ref_distance_trace = go.Scatter(
        x=ref_episode.action_data_table.timestamp[:study_agent_length],
        y=ref_episode.action_data_table["distance"][:study_agent_length],
        name=ref_agent,
    )

    layout_def.update(xaxis=dict(range=[distance_trace.x[0], distance_trace.x[-1]]))

    figure = {
        "data": [
            distance_trace,
            action_trace,
            ref_distance_trace,
            ref_action_trace,
        ],
        "layout": layout_def,
    }

    return figure


def make_rewards_ts(
    study_agent, ref_agent, scenario, reward_figure, cumulative_reward_figure
):
    """
    Make kpi with rewards and cumulated reward for both reference agent and study agent.

    :param study_agent: agent studied
    :param ref_agent: agent to compare with
    :param scenario:
    :param layout: display configuration
    :return: rewards and cumulated rewards for each agents
    """
    study_episode = make_episode(study_agent, scenario)
    ref_episode = make_episode(ref_agent, scenario)
    actions_ts = (
        study_episode.action_data_table.set_index("timestamp")[
            ["action_line", "action_subs", "action_redisp"]
        ]
        .sum(axis=1)
        .to_frame(name="Nb Actions")
    )
    df = observation_model.get_df_computed_reward(study_episode)
    action_events_df = pd.DataFrame(
        index=df["timestep"], data=np.nan, columns=["action_events"]
    )
    action_events_df.loc[
        (actions_ts["Nb Actions"] > 0).values, "action_events"
    ] = df.loc[(actions_ts["Nb Actions"] > 0).values, "rewards"].values
    text = ["<br>-".join(str(act).split("-")) for act in study_episode.actions]
    action_trace = go.Scatter(
        x=action_events_df.index,
        y=action_events_df["action_events"],
        name="Actions",
        mode="markers",
        marker_color="#FFEB3B",
        marker={"symbol": "hexagon", "size": 10},
        text=text,
    )

    ref_reward_trace, ref_reward_cum_trace = ref_episode.reward_trace
    (
        studied_agent_reward_trace,
        studied_agent_reward_cum_trace,
    ) = study_episode.reward_trace
    reward_figure["data"] = [ref_reward_trace, studied_agent_reward_trace, action_trace]
    cumulative_reward_figure["data"] = [
        ref_reward_cum_trace,
        studied_agent_reward_cum_trace,
    ]

    for figure in [reward_figure, cumulative_reward_figure]:
        # Base on the hypothesis that the study agent trace is in position one
        # TODO: clean this up. We should not rely on the position of the study
        # agent in the traces.
        figure["layout"].update(
            {
                "xaxis": {
                    "range": [
                        reward_figure["data"][1].x[0],
                        reward_figure["data"][1].x[-1],
                    ],
                }
            }
        )

    return reward_figure, cumulative_reward_figure


def compute_windows_range(episode, center_idx, n_clicks_left, n_clicks_right):
    """
    Compute the timestamp range for the time window
    :param episode: studied episode
    :param center_idx: timestamp at the center of the range
    :param n_clicks_left: number of times user as click on enlarge left
    :param n_clicks_right: number of times user as click on enlarge right
    :return: the timesteps minimum and maximum
    """
    timestamp_range = episode.timestamps[
        max([0, (center_idx - 10 - 5 * n_clicks_left)]) : (
            center_idx + 10 + 5 * n_clicks_right
        )
    ]
    xmin = timestamp_range[0].strftime("%Y-%m-%dT%H:%M:%S")
    xmax = timestamp_range[-1].strftime("%Y-%m-%dT%H:%M:%S")

    return xmin, xmax
