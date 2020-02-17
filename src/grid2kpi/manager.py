import json
import time

from src.grid2kpi.episode_analytics.EpisodeAnalytics import EpisodeAnalytics
from grid2op.EpisodeData import EpisodeData
import os
import configparser
import csv
import pandas as pd
import pickle

import plotly.graph_objects as go

# TEMPORARY: should be moved to a proper class
from grid2op.PlotPlotly import PlotObs

graph = None


def make_network(new_episode):
    global graph
    if graph is None:
        graph = PlotObs(
            substation_layout=network_layout, observation_space=new_episode.observation_space)
    return graph


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


def make_episode(agent, episode_name):
    if is_in_ram_cache(episode_name, agent):
        return get_from_ram_cache(episode_name, agent)
    elif is_in_fs_cache(episode_name, agent):
        episode = get_from_fs_cache(episode_name, agent)
        save_in_ram_cache(episode_name, agent, episode)
        return episode
    else:
        episode = compute_episode(episode_name, agent)
        save_in_fs_cache(episode_name, agent, episode)
        save_in_ram_cache(episode_name, agent, episode)
        return episode


def clear_fs_cache():
    os.rmdir(cache_dir)


def is_in_fs_cache(episode_name, agent):
    return os.path.isfile(get_fs_cached_file(episode_name, agent))


def get_fs_cached_file(episode_name, agent):
    episode_dir = os.path.join(cache_dir, episode_name)
    if not os.path.exists(episode_dir):
        os.makedirs(episode_dir)
    return os.path.join(episode_dir, agent + ".pickle")


def save_in_fs_cache(episode_name, agent, episode):
    path = get_fs_cached_file(episode_name, agent)
    with open(path, "wb") as f:
        pickle.dump(episode, f)


def get_from_fs_cache(episode_name, agent):
    beg = time.time()
    path = get_fs_cached_file(episode_name, agent)
    with open(path, "rb") as f:
        episode_loaded = pickle.load(f)
    end = time.time()
    print(f"end loading scenario file: {end - beg}")
    return episode_loaded


def compute_episode(episode_name, agent):
    path = base_dir + agent
    return EpisodeAnalytics(EpisodeData.from_disk(
        path, episode_name
    ), episode_name, agent)


def is_in_ram_cache(episode_name, agent):
    return make_ram_cache_id(episode_name, agent) in store


def save_in_ram_cache(episode_name, agent, episode):
    store[make_ram_cache_id(episode_name, agent)] = episode


def get_from_ram_cache(episode_name, agent):
    return store[make_ram_cache_id(episode_name, agent)]


def make_ram_cache_id(episode_name, agent):
    return agent + episode_name


def check_all_tree_and_get_meta_and_best(base_dir, agents):
    best_agents = {}
    meta_json = {}

    for agent in agents:
        for scenario_name in os.listdir(base_dir + agent):
            scenario_folder = os.path.join(base_dir, agent, scenario_name)
            if not os.path.isdir(scenario_folder):
                continue
            with open(os.path.join(scenario_folder, "episode_meta.json")) as f:
                episode_meta = json.load(fp=f)
                meta_json[scenario_name] = episode_meta
                if scenario_name not in best_agents:
                    best_agents[scenario_name] = {"value": -1, "agent": None, "out_of": 0}
                if best_agents[scenario_name]["value"] < episode_meta["nb_timestep_played"]:
                    best_agents[scenario_name]["value"] = episode_meta["nb_timestep_played"]
                    best_agents[scenario_name]["agent"] = agent
                    best_agents[scenario_name]['cum_reward'] = episode_meta['cumulative_reward']
            best_agents[scenario_name]["out_of"] = best_agents[scenario_name]["out_of"] + 1
    return meta_json, best_agents


path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    os.path.pardir,
    os.path.pardir,
    "config.ini"
)

parser = configparser.ConfigParser()
parser.read(path)
base_dir = parser.get("DEFAULT", "base_dir")
cache_dir = os.path.join(base_dir, "_cache")
agents = [file for file in os.listdir(
    base_dir) if os.path.isdir(base_dir + file) and not file.startswith("_")]
meta_json, best_agents = check_all_tree_and_get_meta_and_best(base_dir, agents)
scenarios = []
for agent in agents:
    scen_path = base_dir + agent
    scens = [file for file in os.listdir(
        scen_path) if os.path.isdir(os.path.join(scen_path, file))]
    scenarios = scenarios + scens

scenarios = set(scenarios)

prod_types = {}
network_layout = []
try:
    env_conf_folder = parser.get('DEFAULT', 'env_conf_folder')
    prod_types_file = 'prods_charac.csv'
    network_layout_file = 'coords.csv'
    with open(env_conf_folder + prod_types_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=";")
        line = 0
        for row in csv_reader:
            if line == 0:
                line = line + 1
            else:
                prod_types[row[1]] = row[2]

    with open(env_conf_folder + network_layout_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line = 0
        test = csv_reader
        [network_layout.append(
            (int(row[0].split(',')[1]),
             int(row[0].split(',')[2]))
        ) for row in csv_reader]  # the row is a string which contain the coordinate and an index
except configparser.NoOptionError:
    pass  # ignoring this error
