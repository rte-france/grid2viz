import numpy as np

from .env_actions import env_actions


def total_duration_maintenance(episode):
    timestep_duration = (episode.maintenances.timestamp[1] - episode.maintenances.timestamp[0])
    nb_maintenance = env_actions(episode, which="maintenances", kind="dur", aggr=False).sum()
    return (timestep_duration * nb_maintenance) / np.timedelta64(1, 's') / 60.0


def hist_duration_maintenances(episode):
    # Suppose that there is at most one maintenance per line per episode

    return [t for t in episode.observations[0].duration_next_maintenance if t]

