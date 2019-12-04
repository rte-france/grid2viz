from ..manager import episode
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def get_episode_active_consumption_ts():
    return [sum(obs.load_p) for obs in episode.observations]


def get_total_overflow_ts():
    df = pd.DataFrame(index=range(len(episode.observations)),
                      columns=["time", "value"])
    for (time_step, obs) in enumerate(episode.observations):
        df.loc[time_step, :] = [time_step, (obs.timestep_overflow > 0).sum()]
    return df


def get_total_overflow_trace():
    df = get_total_overflow_ts()
    return go.Scatter(
        x=df["time"],
        y=df["value"]
    )


def get_prod():
    return episode.production


def get_load():
    return episode.load


def get_rho():
    return episode.rho


def get_usage_rate():
    rho = get_rho()
    return rho
    # return rho.groupby("time").aggregate("mean")[["value"]].reset_index()


def get_prod_trace_per_equipment():
    return get_df_trace_per_equipment(get_prod())


def get_usage_rate_trace():
    return get_df_trace_two_dimension(get_usage_rate())


def get_load_trace_per_equipment():
    return get_df_trace_per_equipment(get_load())


def get_df_trace_two_dimension(df):
    return go.Scatter(
        x=df["time"],
        y=df["value"]
    )


def get_df_trace_per_equipment(df):
    trace = []
    for equipment in df["equipment_name"].drop_duplicates():
        trace.append(go.Scatter(
            x=df.loc[df["equipment_name"] == equipment, :]["timestamp"],
            y=df.loc[df["equipment_name"] == equipment, :]["value"],
            name=equipment
        ))
    return trace
