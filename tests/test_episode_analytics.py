import os
import pathlib
import unittest

# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

agents_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "data", "agents")

config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")

from grid2op.Episode.EpisodeData import EpisodeData
from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics
from grid2viz.src.kpi.actions_model import get_action_per_line, get_action_per_sub


class TestEpisodeAnalytics(unittest.TestCase):
    def setUp(self):
        self.agents_path = agents_path
        self.agent_name = "greedy-baseline"
        self.scenario_name = "000"
        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        self.episode_analytics = EpisodeAnalytics(
            self.episode_data, self.scenario_name, self.agent_name
        )

    def test_action_data_table(self):

        self.assertListEqual(
            self.episode_analytics.action_data_table.action_id[:3].tolist(), [0, 1, 2]
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.action_id[37:40].tolist(),
            [4, 3, 0],
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.distance[:3].tolist(), [1, 2, 3]
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.distance[37:40].tolist(), [2, 2, 3]
        )

    def test_action_repartition(self):
        nb_actions = self.episode_analytics.action_data_table[
            ["action_line", "action_subs"]
        ].sum()
        self.assertEqual(nb_actions.action_line, 0.0)
        self.assertEqual(nb_actions.action_subs, 31.0)

        action_per_line = get_action_per_line(self.episode_analytics)
        action_per_sub = get_action_per_sub(self.episode_analytics)

        self.assertListEqual(action_per_line[0].x.tolist(), [])
        # We need to sort the labels for which values are equal.
        # Otherwise, the output is random.
        self.assertListEqual(
            [
                *action_per_sub[0].x.tolist()[:-2],
                *sorted(action_per_sub[0].x.tolist()[-2:]),
            ],
            ["sub_4", "sub_1", "sub_3", "sub_8", "sub_9"],
        )
        self.assertListEqual(action_per_sub[0].y.tolist(), [13, 8, 4, 3, 3])

    def test_multi_topo(self):
        self.agent_name = "multiTopology-baseline"
        self.scenario_name = "000"
        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        self.episode_analytics = EpisodeAnalytics(
            self.episode_data, self.scenario_name, self.agent_name
        )

        nb_actions = self.episode_analytics.action_data_table[
            ["action_line", "action_subs"]
        ].sum()
        self.assertEqual(nb_actions.action_line, 25.0)
        self.assertEqual(nb_actions.action_subs, 38.0)

        action_per_line = get_action_per_line(self.episode_analytics)
        action_per_sub = get_action_per_sub(self.episode_analytics)

        # We need to sort the labels for which values are equal.
        # Otherwise, the output is random.
        self.assertListEqual(sorted(action_per_sub[0].x.tolist()), ["sub_3", "sub_5"])
        self.assertListEqual(action_per_sub[0].y.tolist(), [19, 19])
        self.assertListEqual(action_per_line[0].x.tolist(), ["3_6_15", "9_10_12"])
        self.assertListEqual(action_per_line[0].y.tolist(), [13, 12])

        self.assertListEqual(
            self.episode_analytics.action_data_table.action_id[:5].tolist(),
            [0, 1, 1, 2, 3],
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.distance[:5].tolist(),
            [1, 2, 2, 0, 3],
        )
