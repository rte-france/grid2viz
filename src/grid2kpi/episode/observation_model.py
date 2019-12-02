from ..manager import episode
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def get_episode_active_consumption_ts():

    return [sum(obs.load_p) for obs in episode.observations]


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


def get_all_equipment_active_prod_ts():
    # each time step
    all_ts = {}
    for time_step in range(episode.observations.shape[0]):
        obs = episode.get_observation(time_step)
        if obs.game_over:
            continue
        for equipment in range(len(obs.prod_p)):
            equipment_load = obs.prod_p[equipment]
            if equipment not in all_ts:
                all_ts[equipment] = create_ts_data('equipment', equipment)
            all_ts[equipment]['x'].append(time_step)
            all_ts[equipment]['y'].append(equipment_load)
    return np.asarray(list(all_ts.values()))


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
