import sys

sys.path.insert(0, "D:/Projet/Grid2Op")

from grid2op.EpisodeData import EpisodeData


episode_data = EpisodeData.from_disk(r"D:\Grid2Viz\20200203_agents_118\nodisc_badagent", "0")
