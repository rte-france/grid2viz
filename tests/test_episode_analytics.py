import os
import pathlib
import unittest

os.environ['GRID2VIZ_ROOT'] = ''

from grid2op.Episode.EpisodeData import EpisodeData
from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics
from grid2viz.src.kpi.actions_model import get_action_per_line, get_action_per_sub


class TestEpisodeAnalytics(unittest.TestCase):
    def setUp(self):
        self.agents_path = os.path.join(
            pathlib.Path(__file__).parent.absolute(), 'data', 'agents')
        print(self.agents_path)
        self.agent_name = 'greedy-baseline'
        self.scenario_name = '000'
        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        self.episode_analytics = EpisodeAnalytics(
            self.episode_data, self.scenario_name, self.agent_name
        )

    def test_action_data_table(self):

        self.assertListEqual(
            self.episode_analytics.action_data_table.action_id[:3].tolist(),
            [0, 1, 2]
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.action_id[37:40].tolist(),
            [3, None, 0]
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.distance[:3].tolist(),
            [1, 2, 3]
        )
        self.assertListEqual(
            self.episode_analytics.action_data_table.distance[37:40].tolist(),
            [2, 2, 3]
        )

    def test_action_repartition(self):
        nb_actions = self.episode_analytics.action_data_table[
            ['action_line', 'action_subs']].sum()
        self.assertEqual(nb_actions.action_line, 0.0)
        self.assertEqual(nb_actions.action_subs, 177.0)

        action_per_line = get_action_per_line(self.episode_analytics)
        action_per_sub = get_action_per_sub(self.episode_analytics)

        self.assertListEqual(
            action_per_line[0].x.tolist(),
            []
        )
        self.assertListEqual(
            action_per_sub[0].x.tolist(),
            ['sub_9', 'sub_8', 'sub_4', 'sub_12', 'sub_3', 'sub_1']
        )
        self.assertListEqual(
            action_per_sub[0].y.tolist(),
            [106, 45, 12, 10, 2, 2]
        )



