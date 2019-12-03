from ..manager import episode
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def get_episode_active_consumption_ts():
    return [sum(obs.load_p) for obs in episode.observations]


def get_prod():
    return episode.production


def get_load():
    return episode.load


def get_prod_trace_per_equipment():
    return get_df_trace_per_equipment(get_prod())


def get_all_equipment_active_load_ts():
    # each time step
    all_ts = {}
    for time_step, obs in enumerate(episode.observations):
        if obs.game_over:
            continue
        for equipment in range(len(obs.load_p)):
            equipment_load = obs.load_p[equipment]
            if equipment not in all_ts:
                all_ts[equipment] = create_ts_data('equipment', equipment)
            all_ts[equipment]['x'].append(time_step)
            all_ts[equipment]['y'].append(equipment_load)
    return np.asarray(list(all_ts.values()))


def get_load_trace_per_equipment():
    return get_df_trace_per_equipment(get_load())


def get_df_trace_per_equipment(df):
    trace = []
    for equipment in df["equipment"].drop_duplicates():
        trace.append(go.Scatter(
            x=df.loc[df["equipment"] == equipment, :]["time"],
            y=df.loc[df["equipment"] == equipment, :]["value"]
        ))
    return trace


def create_ts_data(object_type, id):
    return {
        'x': [],
        'y': [],
        'type': 'scatter',
        'name': 'equipment' + str(id),
        'mode': 'lines',
        # 'line': {'color': get_color(object_type, id)}
    }


def get_color(object_type, id):
    return '#'  # TODO : figure out a way to have the same colors everytime
