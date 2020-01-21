from grid2op.Episode import Episode
import os
import configparser
import csv
import pandas as pd

# TEMPORARY: should be moved to a proper class


def get_total_overflow_ts(episode):
    df = pd.DataFrame(index=range(len(episode.observations)),
                      columns=["time", "value"])
    for (time_step, obs) in enumerate(episode.observations):
        tstamp = episode.timestamp(obs)
        tstamp = episode.timestamps[time_step]
        df.loc[time_step, :] = [tstamp, (obs.timestep_overflow > 0).sum()]
    return df


store = {}


def make_episode(base_dir, agent, indx):
    id = agent + indx
    if id in store:
        return store[id]
    path = base_dir + agent
    episode_loaded = Episode.fromdisk(
        path, indx
    )
    store[id] = episode_loaded

    # TEMPORARY: should be moved to a proper class
    setattr(episode_loaded, "total_overflow_ts",
            get_total_overflow_ts(episode_loaded))

    return episode_loaded


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
