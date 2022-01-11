import configparser
import dill
import os
import pathlib
import unittest
from contextlib import redirect_stdout

# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")

from grid2op.Episode.EpisodeData import EpisodeData
from grid2viz.src.kpi.EpisodeAnalytics import EpisodeAnalytics
from grid2op.Episode import EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters
from grid2op.Backend import PandaPowerBackend

try:
    from alphaDeesp.core.grid2op.Grid2opSimulation import (
        Grid2opSimulation,
    )
    from alphaDeesp.expert_operator import expert_operator
except ModuleNotFoundError as ex:
    print(ex)
    print(
        "ExportOp4Grid needs to be installed to run this test. "
        "See https://expertop4grid.readthedocs.io/en/latest/INSTALL.html"
    )
    exit(-1)


class TestExpertAssistSimulation(unittest.TestCase):
    def setUp(self):
        parser = configparser.ConfigParser()
        parser.read(config_file_path)

        self.agents_path = parser.get("DEFAULT", "agents_dir")
        self.cache_dir = os.path.join(self.agents_path, "_cache")
        if not os.path.isdir(self.cache_dir):
            from tests.test_make_cache import TestMakeCache

            test_make_cache = TestMakeCache()
            test_make_cache.setUp()
            test_make_cache.test_make_cache()
        self.agent_name = "do-nothing-baseline"
        self.scenario_name = "000"
        self.env_path = parser.get("DEFAULT", "env_dir")
        p = Parameters()
        p.NO_OVERFLOW_DISCONNECTION = False
        self.env = make(
            self.env_path,
            backend=PandaPowerBackend(),
            test=True,
            param=p,
        )
        self.env.seed(0)
        params_for_runner = self.env.get_params_for_runner()
        params_to_fetch = ["init_grid_path"]
        self.params_for_reboot = {
            key: value
            for key, value in params_for_runner.items()
            if key in params_to_fetch
        }
        self.params_for_reboot["parameters"] = p

        cache_file = os.path.join(
            self.cache_dir, self.scenario_name, self.agent_name + ".dill"
        )
        try:
            with open(cache_file, "rb") as f:
                episode_analytics = dill.load(f)
        except:
            episode_analytics = EpisodeAnalytics(
                self.episode_data, self.scenario_name, self.agent_name
            )
        self.episode_data = EpisodeData.from_disk(
            os.path.join(self.agents_path, self.agent_name), self.scenario_name
        )
        episode_analytics.decorate(self.episode_data)
        episode_analytics.decorate_obs_act_spaces(os.path.join(self.agents_path, self.agent_name))

        self.episode = episode_analytics
        self.act = self.env.action_space()
        self.expert_config = {
            "totalnumberofsimulatedtopos": 25,
            "numberofsimulatedtopospernode": 5,
            "maxUnusedLines": 2,
            "ratioToReconsiderFlowDirection": 0.75,
            "ratioToKeepLoop": 0.25,
            "ThersholdMinPowerOfLoop": 0.1,
            "ThresholdReportOfLine": 0.2,
        }
        self.obs_reboot = None
        self.reward_type = "MinMargin_reward"

    def test_expert(self):
        line_id = 0
        episode_reboot = EpisodeReboot.EpisodeReboot()
        episode_reboot.load(
            PandaPowerBackend(),#self.env.backend,
            data=self.episode,
            agent_path=os.path.join(self.agents_path, self.agent_name),
            name=self.episode.episode_name,
            env_kwargs=self.params_for_reboot,
        )
        obs, *_ = episode_reboot.go_to(1895)
        thermal_limit = self.env.get_thermal_limit()
        new_thermal_limit = thermal_limit.copy()
        flow_ratio = 0.4
        new_thermal_limit[line_id] = flow_ratio / 100.0 * new_thermal_limit[line_id]

        # fictively changing obs.rho and thermal limits to be used by the expert system
        # also making sure that obs thermal_limits are initialized, not to dafault large values as given by reboot
        obs.rho = obs.rho * obs._obs_env.get_thermal_limit() / new_thermal_limit
        obs._obs_env.set_thermal_limit(new_thermal_limit)

        ltc = [line_id]
        with redirect_stdout(None):
            simulator = Grid2opSimulation(
                obs,
                self.env.action_space,self.env.observation_space,
                param_options=self.expert_config,
                debug=False,
                ltc=ltc,
                reward_type=self.reward_type,
            )

            ranked_combinations, expert_system_results, actions = expert_operator(
                simulator, plot=False, debug=False
            )

        expert_system_results = expert_system_results.sort_values(
            ["Topology simulated score", "Efficacity"], ascending=False
        )
        actions = [actions[i] for i in expert_system_results.index]

        episode_reboot = EpisodeReboot.EpisodeReboot()
        episode_reboot.load(
            PandaPowerBackend(),#self.env.backend,
            data=self.episode,
            agent_path=os.path.join(self.agents_path, self.agent_name),
            name=self.episode.episode_name,
            env_kwargs=self.params_for_reboot,
        )
        obs, *_ = episode_reboot.go_to(1895)

        action = actions[0]

        obs, *_ = obs.simulate(action=action, time_step=0)

        assert obs.line_ex_bus[1] == 1
        assert obs.line_ex_bus[4] == 2
        assert obs.line_ex_bus[6] == 2
