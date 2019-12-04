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


# quantiles utilities
def quantile10(df):
    return df.quantile(0.1)


def quantile25(df):
    return df.quantile(0.25)


def quantile75(df):
    return df.quantile(0.75)


def quantile90(df):
    return df.quantile(0.90)


def get_usage_rate():
    rho = get_rho()
    # return rho
    median_rho = rho.groupby("time").aggregate(["median", quantile10, quantile25, quantile75, quantile90])[
        ["value"]].reset_index()
    return median_rho


def get_prod_trace_per_equipment():
    return get_df_trace_per_equipment(get_prod())


def get_load_trace_per_equipment():
    return get_df_trace_per_equipment(get_load())


def get_usage_rate_trace():
    df = get_usage_rate()
    line = {
        "shape": "spline",
        "width": 0,
        "smoothing": 1
    }
    trace = [go.Scatter(
        x=df["time"],
        y=df["value"]["quantile10"],
        name="quantile 10",
        line=line
    ), go.Scatter(
        x=df["time"],
        y=df["value"]["quantile25"],
        name="quantile 25",
        fill="tonexty",
        fillcolor="rgba(159, 197, 232, 0.63)",
        line=line
    ), go.Scatter(
        x=df["time"],
        y=df["value"]["median"],
        name="median",
        fill="tonexty",
        fillcolor="rgba(31, 119, 180, 0.5)",
        line={
            "color": "rgb(31, 119, 180)",
            "shape": "spline",
            "smoothing": 1
        }
    ), go.Scatter(
        x=df["time"],
        y=df["value"]["quantile75"],
        name="quantile 75",
        fill="tonexty",
        fillcolor="rgba(31, 119, 180, 0.5)",
        line=line
    ), go.Scatter(
        x=df["time"],
        y=df["value"]["quantile90"],
        name="quantile 90",
        fill="tonexty",
        fillcolor="rgba(159, 197, 232, 0.63)",
        line=line
    )]
    return trace


def get_df_trace_per_equipment(df):
    trace = []
    for equipment in df["equipment_name"].drop_duplicates():
        trace.append(go.Scatter(
            x=df.loc[df["equipment_name"] == equipment, :]["timestamp"],
            y=df.loc[df["equipment_name"] == equipment, :]["value"],
            name=equipment
        ))
    return trace
