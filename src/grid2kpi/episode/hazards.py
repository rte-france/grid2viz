from ..manager import episode


def getHazardTs():
    return episode.get_observation(0)
