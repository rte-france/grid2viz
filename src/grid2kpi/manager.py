from grid2op.Episode import Episode
from functools import partial

indx = 1
path = f"D:/Projects/RTE - Grid2Viz/grid2op/getting_started/study_agent_getting_started/"

episode = Episode.fromdisk(
    path, indx
)


for obs in episode.observations:
    print(obs.load_p)
    break

print(episode.observations[700].load_p)
