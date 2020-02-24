"""
    Utility functions for creation of graph and graph component used several times.
"""
from plotly import graph_objects as go
from grid2kpi.episode import EpisodeTrace
from grid2kpi.episode.actions_model import get_actions_sum

from grid2viz.manager import make_episode


def ts_graph_avail_assets(ts_kind, episode, prod_types):
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
        options, value = [{'label': line_name, 'value': line_name}
                          for line_name in [*episode.line_names, 'total']], episode.line_names[0]
    elif ts_kind == 'Production':
        options = [{'label': prod_name,
                    'value': prod_name}
                   for prod_name in [*episode.prod_names, *list(set(prod_types.values())), 'total']]
        value = episode.prod_names[0]
    else:
        options = [{'label': load_name,
                    'value': load_name}
                   for load_name in [*episode.load_names, 'total']]
        value = episode.load_names[0]

    return options, value


def environment_ts_data(kind, episode, equipments, prod_types):
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

        if action['has_impact']:
            injection = action['injection']
            force_line = action['force_line']
            switch_line = action['switch_line']
            topology = action['topology']

            if injection['changed']:
                [impact_append(" injection set {} to {} <br>"
                               .format(detail['set'], detail['to']))
                 for detail in injection['impacted']]

            if force_line['changed']:
                reconnections = force_line['reconnections']
                disconnections = force_line['disconnections']

                if reconnections['count'] > 0:
                    impact_append(" force reconnection of {} powerlines ({}) <br>"
                                  .format(reconnections['count'], reconnections['powerlines']))

                if disconnections['count'] > 0:
                    impact_append(" force disconnection of {} powerlines ({}) <br>"
                                  .format(disconnections['count'], disconnections['powerlines']))

            if switch_line['changed']:
                impact_append(" switch status of {} powerlines ({}) <br>"
                              .format(switch_line['count'], switch_line['powerlines']))

            if topology['changed']:
                bus_switch = topology['bus_switch']
                assigned_bus = topology['assigned_bus']
                disconnected_bus = topology['disconnect_bus']

                if len(bus_switch) > 0:
                    [impact_append(" switch bus of {} {} on substation {} <br>"
                                   .format(switch['object_type'], switch['object_id'],
                                           switch['substation']))
                     for switch in bus_switch]

                if len(assigned_bus) > 0:
                    [impact_append(" assign bus {} to {} {} on substation {} <br>"
                                   .format(assignment['bus'], assignment['object_type'],
                                           assignment['object_id'], assignment['substation']))
                     for assignment in assigned_bus]

                if len(disconnected_bus) > 0:
                    [impact_append(" disconnect bus {} {} on substation {} <br>"
                                   .format(disconnection['object_type'], disconnection['object_id'],
                                           disconnection['substation']))
                     for disconnection in disconnected_bus]

            tooltip_append(''.join(impact_detail))
        else:
            tooltip_append('Do nothing')

    return tooltip


def action_ts(study_agent, ref_agent, scenario, figure):
    """
    Make the action timeseries trace of study and reference agents.

    :param study_agent: studied agent to compare
    :param ref_agent: reference agent to compare with
    :param scenario:
    :param figure: figure on layout page
    :return: nb action and distance for each agents
    """
    ref_episode = make_episode(ref_agent, scenario)
    study_episode = make_episode(study_agent, scenario)
    actions_ts = get_actions_sum(study_episode)
    ref_agent_actions_ts = get_actions_sum(ref_episode)
    figure["data"] = [
        go.Scatter(x=study_episode.action_data_table.timestamp,
                   y=actions_ts["Nb Actions"], name=study_agent,
                   text=action_tooltip(study_episode.actions)),
        go.Scatter(x=ref_episode.action_data_table.timestamp,
                   y=ref_agent_actions_ts["Nb Actions"], name=ref_agent,
                   text=action_tooltip(ref_episode.actions)),

        go.Scatter(x=study_episode.action_data_table.timestamp,
                   y=study_episode.action_data_table["distance"], name=study_agent + " distance", yaxis='y2'),
        go.Scatter(x=ref_episode.action_data_table.timestamp,
                   y=ref_episode.action_data_table["distance"], name=ref_agent + " distance", yaxis='y2'),
    ]
    figure['layout'] = {**figure['layout'],
                        'yaxis': {'title': 'Actions'},
                        'yaxis2': {'title': 'Distance', 'side': 'right', 'anchor': 'x', 'overlaying': 'y'}}
    return figure
