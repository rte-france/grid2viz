import json
import time

from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics
from grid2op.EpisodeData import EpisodeData
import os
import configparser
import csv
import pickle

from grid2op.Plot import PlotPlotly

graph = None


def make_network(episode):
    """
        Create a Plotly network graph with the layout configuration and the selected episode.

        :param episode: An episode containing targeted data for the graph.
        :return: Network graph
    """
    global graph
    if graph is None:
        graph = PlotPlotly(
            substation_layout=network_layout, observation_space=episode.observation_space)
    return graph


store = {}


def make_episode(agent, episode_name):
    """
        Load episode from cache. If not already in, compute episode data
        and save it in cache.

        :param agent: Agent Name
        :param episode_name: Name of the studied episode
        :return: Episode with computed data
    """
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
        pickle.dump(episode, f, protocol=4)


def get_from_fs_cache(episode_name, agent):
    beg = time.time()
    path = get_fs_cached_file(episode_name, agent)
    with open(path, "rb") as f:
        episode_loaded = pickle.load(f)
    end = time.time()
    print(f"end loading scenario file: {end - beg}")
    return episode_loaded


def compute_episode(episode_name, agent):
    path = os.path.join(agents_dir, agent)
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
        for scenario_name in os.listdir(os.path.join(base_dir, agent)):
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


"""
Initialisation routine
"""
''' Parsing of config file'''
path_cfg = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")
parser = configparser.ConfigParser()
print("the config file used is located at: {}".format(path_cfg))
parser.read(path_cfg)

agents_dir = parser.get("DEFAULT", "agents_dir")
print("Agents data used is located at: {}".format(agents_dir))
cache_dir = os.path.join(agents_dir, "_cache")
'''Parsing of agent folder tree'''
agents = sorted([file for file in os.listdir(agents_dir)
                 if os.path.isdir(os.path.join(agents_dir, file)) and not file.startswith("_")])
meta_json, best_agents = check_all_tree_and_get_meta_and_best(agents_dir, agents)
scenarios = []
for agent in agents:
    scen_path = os.path.join(agents_dir, agent)
    scens = [file for file in os.listdir(
        scen_path) if os.path.isdir(os.path.join(scen_path, file))]
    scenarios = scenarios + scens

scenarios = set(scenarios)

'''Parsing of the environment configuration'''
env_conf_folder = parser.get('DEFAULT', 'env_dir')
print("Environment used is located at: {}".format(env_conf_folder))
network_layout = []
try:
    network_layout_file = 'coords.csv'
    with open(os.path.join(env_conf_folder, network_layout_file)) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        line = 0  # skip the header part
        for coords in csv_reader:
            if line == 0:
                line = line + 1
                continue
            network_layout.append(
                (int(coords[0]),
                 int(coords[1]))
            )
except configparser.NoOptionError as ex:
    pass  # ignoring this error
except FileNotFoundError as e:
    pass  # ignoring that too
