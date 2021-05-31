import os
import pathlib
import unittest

# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

agents_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "data", "agents")

config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")


from grid2op import make
from grid2op.Backend import PandaPowerBackend
from grid2op.Episode.EpisodeData import EpisodeData
from grid2op.Parameters import Parameters
from grid2op.Runner import Runner

from CustomAgent import RandomRedispatchAgent
from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics


class TestGenerateAgent(unittest.TestCase):
    def setUp(self):
        self.case = "rte_case14_realistic"
        self.backend = PandaPowerBackend()
        self.param = Parameters()

        self.agents_path = agents_path
        self.agent_name = "redispatching-baseline"
        self.scenario_name = "000"

    def test_generate_and_read_agent_redisp(self):
        with make(self.case, param=self.param, backend=self.backend) as env:
            agent = RandomRedispatchAgent(env.action_space, env)
            runner = Runner(
                **env.get_params_for_runner(), agentClass=None, agentInstance=agent
            )
            # need to be seeded for reproducibility as this takes random redispatching actions
            runner.run(
                nb_episode=1,
                path_save=os.path.join(self.agents_path, self.agent_name),
                nb_process=1,
                max_iter=10,
                env_seeds=[0],
                agent_seeds=[0],
                pbar=True,
            )
            env.close()

        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        self.episode_analytics = EpisodeAnalytics(
            self.episode_data, self.scenario_name, self.agent_name
        )
