

def action_tooltip(episode_actions):
    """
        This is used to get a detailled impact action in tooltip format in order to diplay this tooltip on a
        plotly graph

        Parameters
        ----------
        episode_actions: :class:`grid2viz.grid2Kpi.EpisodeAnalytics`
            Representation of the episode used in the scenario

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
