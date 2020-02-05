import numpy as np
import pandas as pd
import plotly.graph_objects as go
from .env_actions import env_actions


def get_prod_and_conso(episode):
    episode_data = episode['data']
    productions = pd.pivot_table(
        episode_data.production, index="timestamp", values="value",
        columns=["equipment_name"]
    )

    loads = pd.pivot_table(
        episode_data.load, index="timestamp", values="value",
        columns=["equipment_name"]
    )

    prods_and_loads = productions.merge(
        loads, left_index=True, right_index=True)
    return prods_and_loads


def get_episode_active_consumption_ts(episode):
    return [sum(obs.load_p) for obs in episode['data'].observations]


def get_prod(episode, equipments=None):
    if equipments is None:
        return episode['data'].production
    else:
        return episode['data'].production.loc[episode['data'].production.equipment_name.isin(equipments), :]


def get_load(episode, equipments=None):
    if equipments is None:
        return episode['data'].load
    else:
        return episode['data'].load.loc[episode['data'].load.equipment_name.isin(equipments), :]


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
    median_rho = rho.groupby("timestamp").aggregate(["median", quantile10, quantile25, quantile75, quantile90, "max"])[
        ["value"]].reset_index()
    return median_rho


def get_duration_maintenances(episode):
    timestep_duration = (episode['data'].timestamps[1] - episode['data'].timestamps[0])
    nb_maintenance = env_actions(episode, which="maintenances", kind="dur", aggr=False).sum()
    return (timestep_duration * nb_maintenance).total_seconds() / 60.0


def init_table_inspection_data(episode):
    ts_hazards = env_actions(episode, which="hazards", kind="ts", aggr=True)
    ts_maintenances = env_actions(
        episode, which="maintenances", kind="ts", aggr=True)
    table = ts_hazards.merge(
        ts_maintenances, left_index=True, right_index=True)
    table = table.reset_index()
    table["IsWorkingDay"] = table["timestamp"].dt.weekday < 5
    return table
