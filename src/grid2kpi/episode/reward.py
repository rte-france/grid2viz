from ..manager import episode
import pandas as pd


def get_line_usage_ts():
    df = pd.DataFrame(index=range(len(episode.observations)), columns=["time", "value", "q50", "q90"])
    for (time_step, obs) in enumerate(episode.observations):
        df.loc[time_step, :] = [time_step, obs.timestep_overflow.sum()]
    return df
