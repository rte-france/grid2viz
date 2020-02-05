from src.grid2kpi.episode_analytics import EpisodeTrace
from src.grid2kpi.episode_analytics.EpisodeAnalytics import EpisodeAnalytics
from grid2op.EpisodeData import EpisodeData
import os
import configparser
import csv
import pandas as pd

import plotly.graph_objects as go

# TEMPORARY: should be moved to a proper class
from grid2op.PlotPlotly import PlotObs


graphs = {}
graph_layout = [(280, -81), (100, -270), (-366, -270), (-366, -54), (64, -54), (64, 54), (-450, 0),
                (-550, 0), (-326, 54), (-222, 108), (-79, 162), (170, 270), (64, 270), (-222, 216)]


def make_network(new_episode):
    if new_episode not in graphs:
        graphs[new_episode] = PlotObs(
            substation_layout=graph_layout, observation_space=new_episode.observation_space)
    return graphs[new_episode]


def get_network_graph(network, episode):
    fig_dict = network.get_plot_observation(episode.observations[0]).to_dict()
    fig_dict["frames"] = []
    fig_dict["layout"]["sliders"] = {
        "args": [
            "transition", {
                "duration": 400,
                "easing": "cubic-in-out"
            }
        ],
        "initialValue": str(episode.timestamp(episode.observations[0])),
        "plotlycommand": "animate",
        "values": episode.timestamps,
        "visible": True
    }
    fig_dict["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 500, "redraw": False},
                                    "fromcurrent": True, "transition": {"duration": 300,
                                                                        "easing": "quadratic-in-out"}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Timestamp:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": []
    }
    for obs in episode.observations[:-1]:
        timestamp = episode.timestamp(obs)
        frame = {"data": [], "name": str(timestamp)}
        current_fig_dict = network.get_plot_observation(obs).to_dict()
        frame["data"] = current_fig_dict["data"]
        fig_dict["frames"].append(frame)
        slider_step = {"args": [
            [timestamp],
            {"frame": {"duration": 300, "redraw": False},
             "mode": "immediate",
             "transition": {"duration": 300}}
        ],
            "label": str(timestamp),
            "method": "animate"}
        sliders_dict["steps"].append(slider_step)

    fig_dict["layout"]["sliders"] = [sliders_dict]

    fig = go.Figure(fig_dict)

    return fig


store = {}


def make_episode(base_dir, agent, indx):
    id = agent + indx
    if id in store:
        return store[id]
    path = base_dir + agent
    episode_loaded = EpisodeAnalytics(EpisodeData.fromdisk(
        path, indx
    ))
    store[id] = {
        'data': episode_loaded,
        'total_overflow_trace': EpisodeTrace.get_total_overflow_trace(episode_loaded),
        'usage_rate_trace': EpisodeTrace.get_usage_rate_trace(episode_loaded),
        'reward_trace': EpisodeTrace.get_df_rewards_trace(episode_loaded, id + '_rewards', id + '_cum_rewards'),
        'total_overflow_ts': EpisodeTrace.get_total_overflow_ts(episode_loaded)
    }

    return store[id]


path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    os.path.pardir,
    os.path.pardir,
    "config.ini"
)

parser = configparser.ConfigParser()
parser.read(path)

indx = parser.get("DEFAULT", "scenario")
base_dir = parser.get("DEFAULT", "base_dir")
agent_ref = parser.get("DEFAULT", "agent_ref")
episode = make_episode(base_dir, agent_ref, indx)
agents = [file for file in os.listdir(
    base_dir) if os.path.isdir(base_dir + file)]
scenarios = []
for agent in agents:
    scen_path = base_dir + agent
    scens = [file for file in os.listdir(
        scen_path) if os.path.isdir(os.path.join(scen_path, file))]
    scenarios = scenarios + scens

scenarios = set(scenarios)

prod_types = {}
try:
    prod_types_file = parser.get("DEFAULT", "prod_types")
    if prod_types_file is not None:
        with open(base_dir + prod_types_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line = 0
            for row in csv_reader:
                if line == 0:
                    line = line + 1
                else:
                    prod_types[row[1]] = row[2]
except configparser.NoOptionError:
    pass  # ignoring this error
