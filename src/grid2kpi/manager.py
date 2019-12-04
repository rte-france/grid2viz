from grid2op.Episode import Episode
import os
import configparser

path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    os.path.pardir,
    os.path.pardir,
    "config.ini"
)

parser = configparser.ConfigParser()
parser.read(path)

indx = parser.get("DEFAULT", "scenario")
path = parser.get("DEFAULT", "base_dir")
episode = Episode.fromdisk(
    path, indx
)
