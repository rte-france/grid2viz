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
from grid2viz.src.simulation.simulation_utils import action_dict_from_choose_tab
from grid2op.Episode import EpisodeReboot
from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters
from grid2op.Backend import PandaPowerBackend


class TestChooseSimulation(unittest.TestCase):
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
        self.episode = episode_analytics
        self.episode_reboot = EpisodeReboot.EpisodeReboot()
        self.episode_reboot.load(
            PandaPowerBackend(),#self.env.backend,
            data=self.episode,
            agent_path=os.path.join(self.agents_path, self.agent_name),
            name=self.episode.episode_name,
            env_kwargs=self.params_for_reboot,
        )
        self.obs, *_ = self.episode_reboot.go_to(1895)
        self.act = self.env.action_space()

    def test_line_disconnect(self):
        params_dict = dict(
            ex_or_lines="",
            target_lines="Status",
            disc_rec_lines="Disconnect",
        )
        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Lines",
            selected_object="0_1_0",
            topology_type="Set",
            params_dict=params_dict,
        )
        assert "set_line_status" in action_dict.keys()
        assert action_dict["set_line_status"] == [(0, -1)]

        self.act.update(action_dict)
        obs, *_ = self.obs.simulate(action=self.act, time_step=0)

        # Check line_id 0 has been disconnected
        assert not obs.line_status[0]

    def test_line_set_bus(self):
        params_dict = dict(
            ex_or_lines="Ex",
            target_lines="Bus",
            disc_rec_lines="",
        )
        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Lines",
            selected_object="0_1_0",
            bus="Bus2",
            topology_type="Set",
            params_dict=params_dict,
        )
        assert "set_bus" in action_dict.keys()
        assert "lines_ex_id" in action_dict["set_bus"]
        assert action_dict["set_bus"]["lines_ex_id"] == [(0, 2)]

        self.act.update(action_dict)
        obs, *_ = self.obs.simulate(action=self.act, time_step=0)

        assert obs.line_ex_bus[0] == 2

    def test_line_change_bus(self):
        params_dict = dict(
            ex_or_lines="Or",
            target_lines="Bus",
            disc_rec_lines="",
        )
        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Lines",
            selected_object="0_1_0",
            topology_type="Change",
            params_dict=params_dict,
        )
        assert "change_bus" in action_dict.keys()
        assert "lines_or_id" in action_dict["change_bus"]
        assert action_dict["change_bus"]["lines_or_id"] == [0]

        self.act.update(action_dict)
        obs, *_ = self.obs.simulate(action=self.act, time_step=0)

        assert obs.line_or_bus[0] == 2

    def test_load_change_bus(self):

        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Loads",
            selected_object="load_1_0",
            topology_type="Change",
        )

        assert "change_bus" in action_dict.keys()
        assert "loads_id" in action_dict["change_bus"]
        assert action_dict["change_bus"]["loads_id"][0] == 0

        self.act.update(action_dict)
        obs, reward, done, _ = self.obs.simulate(action=self.act, time_step=0)

        # Game over
        assert done

    def test_load_set_bus(self):
        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Loads",
            selected_object="load_1_0",
            topology_type="Set",
            bus="Bus2",
        )

        assert "set_bus" in action_dict.keys()
        assert "loads_id" in action_dict["set_bus"]
        assert action_dict["set_bus"]["loads_id"] == [(0, 2)]

        self.act.update(action_dict)
        obs, reward, done, _ = self.obs.simulate(action=self.act, time_step=0)

        # Game over
        assert done

    def test_redispatch(self):
        params_dict = dict(
            redisp_volume=3,
            action_type_gens="Redispatch",
        )
        action_dict = action_dict_from_choose_tab(
            self.episode,
            kind="Gens",
            selected_object="gen_1_0",
            params_dict=params_dict,
        )

        assert "redispatch" in action_dict.keys()
        assert action_dict["redispatch"][0] == 3.0

        self.act.update(action_dict)
        initial_gen_p = self.obs.gen_p[0]
        obs, reward, done, _ = self.obs.simulate(action=self.act, time_step=0)

        assert initial_gen_p + 3.0 == obs.gen_p[0]
