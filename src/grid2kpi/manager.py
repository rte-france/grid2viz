from grid2op.Episode import Episode
import os
import configparser


def make_episode(base_dir, agent_ref, indx):
    path = base_dir + agent_ref
    return Episode.fromdisk(
        path, indx
    )


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
    base_dir) if os.path.isdir(base_dir+file)]
scenarios = []
for agent in agents:
    scen_path = base_dir + agent
    scens = [file for file in os.listdir(
        scen_path) if os.path.isdir(os.path.join(scen_path, file))]
    scenarios = scenarios + scens

scenarios = set(scenarios)
