from grid2op.Episode import Episode

indx = 1
path = f"D:/Projets/Package Artelys_DebutPrestationArtelys/20191201_agentslog/nodisc_powerlinegreedy/"

episode = Episode.fromdisk(
    path, indx
)
