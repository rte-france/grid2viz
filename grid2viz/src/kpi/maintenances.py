# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

from .env_actions import env_actions


def total_duration_maintenance(episode):
    timestep_duration = episode.timestamps[1] - episode.timestamps[0]
    nb_maintenance = env_actions(
        episode, which="maintenances", kind="dur", aggr=False
    ).sum()
    return (timestep_duration * nb_maintenance).total_seconds() / 60.0


def hist_duration_maintenances(episode):
    # Suppose that there is at most one maintenance per line per episode

    return [t for t in episode.observations[0].duration_next_maintenance if t]
