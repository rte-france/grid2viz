"""
Functions shared between micro_clbk and micro_lyt
"""


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
                      max([0, (center_idx - 10 - 5 * n_clicks_left)]):(center_idx + 10 + 5 * n_clicks_right)
                      ]
    xmin = timestamp_range[0].strftime("%Y-%m-%dT%H:%M:%S")
    xmax = timestamp_range[-1].strftime("%Y-%m-%dT%H:%M:%S")

    return xmin, xmax
