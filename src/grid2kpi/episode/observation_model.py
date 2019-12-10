from ..manager import episode
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .env_actions import env_actions


def get_prod_and_conso():
    productions = pd.pivot_table(
        episode.production, index="timestamp", values="value",
        columns=["equipment_name"]
    )

    loads = pd.pivot_table(
        episode.load, index="timestamp", values="value",
        columns=["equipment_name"]
    )

    prods_and_loads = productions.merge(
        loads, left_index=True, right_index=True)
    return prods_and_loads


def get_episode_active_consumption_ts():
    return [sum(obs.load_p) for obs in episode.observations]


def get_total_overflow_ts(episode):
    df = pd.DataFrame(index=range(len(episode.observations)),
                      columns=["time", "value"])
    for (time_step, obs) in enumerate(episode.observations):
        tstamp = episode.timestamp(obs)
        df.loc[time_step, :] = [tstamp, (obs.timestep_overflow > 0).sum()]
    return df


def get_total_overflow_trace(episode):
    df = get_total_overflow_ts(episode)
    return [go.Scatter(
        x=df["time"],
        y=df["value"],
        name="Nb of overflows"
    )]


def get_prod():
    return episode.production


def get_load():
    return episode.load


def get_rho(episode):
    return episode.rho


def get_df_computed_reward(episode):
    return episode.computed_reward


# quantiles utilities
def quantile10(df):
    return df.quantile(0.1)


def quantile25(df):
    return df.quantile(0.25)


def quantile75(df):
    return df.quantile(0.75)


def quantile90(df):
    return df.quantile(0.90)


def get_usage_rate(episode):
    rho = get_rho(episode)
    # return rho
    median_rho = rho.groupby("timestamp").aggregate(["median", quantile10, quantile25, quantile75, quantile90])[
        ["value"]].reset_index()
    return median_rho


def get_hazard_trace():
    ts_hazards_by_line = env_actions(
        episode, which="hazards", kind="ts", aggr=False)
    trace = [go.Scatter(x=ts_hazards_by_line.index, y=ts_hazards_by_line[line],
                        name=line)
             for line in ts_hazards_by_line.columns]
    return trace


def get_maintenance_trace():
    ts_maintenances_by_line = env_actions(
        episode, which="maintenances", kind="ts", aggr=False)
    trace = [go.Scatter(x=ts_maintenances_by_line.index,
                        y=ts_maintenances_by_line[line],
                        name=line)
             for line in ts_maintenances_by_line.columns]
    return trace


def get_prod_trace_per_equipment():
    return get_df_trace_per_equipment(get_prod())


def get_load_trace_per_equipment():
    return get_df_trace_per_equipment(get_load())


def get_usage_rate_trace(episode):
    df = get_usage_rate(episode)
    line = {
        "shape": "spline",
        "width": 0,
        "smoothing": 1
    }
    trace = [go.Scatter(
        x=df["timestamp"],
        y=df["value"]["quantile10"],
        name="quantile 10",
        line=line
    ), go.Scatter(
        x=df["timestamp"],
        y=df["value"]["quantile25"],
        name="quantile 25",
        fill="tonexty",
        fillcolor="rgba(159, 197, 232, 0.63)",
        line=line
    ), go.Scatter(
        x=df["timestamp"],
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
        x=df["timestamp"],
        y=df["value"]["quantile75"],
        name="quantile 75",
        fill="tonexty",
        fillcolor="rgba(31, 119, 180, 0.5)",
        line=line
    ), go.Scatter(
        x=df["timestamp"],
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


def init_table_inspection_data():
    ts_hazards = env_actions(episode, which="hazards", kind="ts", aggr=True)
    ts_hazards = ts_hazards.rename(columns={"value": "Hazards"})
    ts_maintenances = env_actions(
        episode, which="maintenances", kind="ts", aggr=True)
    ts_maintenances = ts_maintenances.rename(columns={"value": "Maintenances"})
    table = ts_hazards.merge(
        ts_maintenances, left_index=True, right_index=True)
    table = table.reset_index()
    table["IsWorkingDay"] = table["timestamp"].dt.weekday < 5
    return table


def get_df_rewards_trace(episode):
    trace = []
    df = get_df_computed_reward(episode)
    trace.append(go.Scatter(x=df["timestep"], y=df["rewards"], name="rewards"))
    trace.append(go.Scatter(x=df["timestep"], y=df["cum_rewards"], name="cum_rewards", yaxis='y2'))
    return trace
