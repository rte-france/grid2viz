from grid2kpi.episode_analytics.env_actions import env_actions


def nb_maintenances(episode):
    # Suppose that there is at most one maintenance per line per episode

    return sum(
        1 for t in episode.observations[0].duration_next_maintenance if t
    )


def duration_maintenances(episode):
    # Suppose that there is at most one maintenance per line per episode
    return sum(
        t for t in episode.observations[0].duration_next_maintenance if t
    )


def total_duration_maintenance(episode):
    timestep_duration = (episode.timestamps[1] - episode.timestamps[0])
    nb_maintenance = env_actions(episode, which="maintenances", kind="dur", aggr=False).sum()
    return (timestep_duration * nb_maintenance).total_seconds() / 60.0


def hist_duration_maintenances(episode):
    # Suppose that there is at most one maintenance per line per episode

    return [t for t in episode.observations[0].duration_next_maintenance if t]

