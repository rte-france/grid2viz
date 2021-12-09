import os
import pathlib
import unittest

# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config_tests.ini")

agents_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "data", "agents")


from grid2op.Backend import PandaPowerBackend
from grid2op.Episode.EpisodeData import EpisodeData
from grid2op.Parameters import Parameters

from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics
from grid2viz.src.manager import make_network


class TestPlotAgent(unittest.TestCase):
    def setUp(self):
        self.case = "rte_case14_realistic"

        self.backend = PandaPowerBackend()
        self.param = Parameters()

        self.agents_path = agents_path
        self.agent_name = "redispatching-baseline"
        self.scenario_name = "000"

    def test_plot(self):
        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        self.episode_analytics = EpisodeAnalytics(
            self.episode_data, self.scenario_name, self.agent_name
        )
        self.episode_analytics.decorate(self.episode_data)

        make_network(self.episode_analytics).plot_obs(
            self.episode_analytics.observations[0]
        )
