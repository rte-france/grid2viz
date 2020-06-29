import datetime as dt
import time

from .env_actions import env_actions
from grid2op.Episode import EpisodeData
import numpy as np
import pandas as pd
from tqdm import tqdm

from . import EpisodeTrace, maintenances, consumption_profiles


class EpisodeAnalytics:
    def __init__(self, episode_data, episode_name, agent):
        self.episode_name = episode_name
        self.agent = agent



        self.timesteps = list(range(len(episode_data.actions)))
        print("computing df")
        beg = time.time()
        print("Environment")
        self.load, self.production, self.rho, self.action_data_table, self.computed_reward, self.flow_and_voltage_line = self._make_df_from_data(episode_data)
        print("Hazards-Maintenances")
        self.hazards, self.maintenances = self._env_actions_as_df(episode_data)
        print("Computing computation intensive indicators...")
        self.total_overflow_trace = EpisodeTrace.get_total_overflow_trace(self, episode_data)
        self.usage_rate_trace = EpisodeTrace.get_usage_rate_trace(self)
        self.reward_trace = EpisodeTrace.get_df_rewards_trace(self)
        self.total_overflow_ts = EpisodeTrace.get_total_overflow_ts(self, episode_data)
        self.profile_traces = consumption_profiles.profiles_traces(self)
        self.total_maintenance_duration = maintenances.total_duration_maintenance(self)
        self.nb_hazards = env_actions(self, which="hazards", kind="nb", aggr=True)
        self.nb_maintenances = env_actions(self, which="maintenances", kind="nb", aggr=True)

        end = time.time()
        print(f"end computing df: {end - beg}")

    @staticmethod
    def timestamp(obs):
        return dt.datetime(obs.year, obs.month, obs.day, obs.hour_of_day,
                           obs.minute_of_hour)

    # @jit(forceobj=True)
    def _make_df_from_data(self, episode_data):
        """
        Convert all episode's data into comprehensible dataframes usable by
        the application.

        The generated dataframes are:
            - loads
            - production
            - rho
            - action data table
            - instant and cumulated rewards
            - flow and voltage by line

        Returns
        -------
        res: :class:`tuple`
         generated dataframes
        """
        size = len(episode_data.actions)
        timesteps = list(range(size))
        load_size = size * len(episode_data.observations[0].load_p)
        prod_size = size * len(episode_data.observations[0].prod_p)
        n_rho = len(episode_data.observations[0].rho)
        rho_size = size * n_rho

        load_data = pd.DataFrame(index=range(load_size),
                                 columns=["timestamp", "value"])
        load_data.loc[:, "value"] = load_data.loc[:, "value"].astype(float)

        production = pd.DataFrame(index=range(prod_size),
                                  columns=["value"])

        rho = pd.DataFrame(index=range(rho_size), columns=['value'])

        cols_loop_action_data_table = [
            'action_line', 'action_subs', 'line_name', 'sub_name',
            'objects_changed', 'distance'
        ]
        action_data_table = pd.DataFrame(
            index=range(size),
            columns=[
                'timestep', 'timestamp', 'timestep_reward', 'action_line',
                'action_subs', 'line_name', 'sub_name', 'objects_changed',
                'distance'
            ]
        )

        computed_rewards = pd.DataFrame(index=range(size),
                                        columns=['timestep', 'rewards', 'cum_rewards'])
        flow_voltage_cols = pd.MultiIndex.from_product(
            [['or', 'ex'], ['active', 'reactive', 'current', 'voltage'], episode_data.line_names])
        flow_voltage_line_table = pd.DataFrame(index=range(size), columns=flow_voltage_cols)

        topo_list = []
        bus_list = []
        for (time_step, (obs, act)) in tqdm(enumerate(zip(episode_data.observations[:-1], episode_data.actions)),
                                            total=size):
            time_stamp = self.timestamp(obs)
            line_impact, sub_impact = act.get_topological_impact()
            sub_action = act.name_sub[sub_impact]
            line_name = episode_data.line_names[line_impact]

            if not len(sub_action):
                sub_action = None
            else: 
                sub_action = " - ".join(sub_action)
            if not len(line_name):
                line_name = None
            else: 
                line_name = " - ".join(line_name)

            # Building load DF
            begin = time_step * episode_data.n_loads
            end = (time_step + 1) * episode_data.n_loads - 1
            load_data.loc[begin:end, "value"] = obs.load_p.astype(float)
            load_data.loc[begin:end, "timestamp"] = time_stamp
            # Building prod DF
            begin = time_step * episode_data.n_prods
            end = (time_step + 1) * episode_data.n_prods - 1
            production.loc[begin:end, "value"] = obs.prod_p.astype(float)
            # Building RHO DF
            begin = time_step * n_rho
            end = (time_step + 1) * n_rho - 1
            rho.loc[begin:end, "value"] = obs.rho.astype(float)

            pos = time_step
            # TODO : change with benjamin's count of actions
            action_line = np.sum(act._switch_line_status) + np.sum(act._set_line_status)
            if action_line > 0:
                line_name = "reconnect " + line_name
            if action_line < 0:
                line_name = "disconnect " + line_name
                action_line = - action_line

            # TODO: change with benjamin's count of actions
            action_subs = int(np.any(act._change_bus_vect)) + int(np.any(act._set_topo_vect))
            if action_line:
                action_subs = 0

            object_changed_set = self.get_object_changed(
                act._set_topo_vect, topo_list)
            if object_changed_set is not None:
                object_changed = object_changed_set
            else:
                object_changed = self.get_object_changed(
                    act._change_bus_vect, bus_list)

            action_data_table.loc[pos, cols_loop_action_data_table] = [
                action_line,
                action_subs,
                line_name,
                sub_action,
                object_changed,
                self.get_distance_from_obs(obs)]

            computed_rewards.loc[time_step, :] = [
                time_stamp,
                episode_data.rewards[time_step],
                episode_data.rewards.cumsum(axis=0)[time_step]
            ]

            flow_voltage_line_table.loc[time_step, :] = np.array([
                obs.p_ex,
                obs.q_ex,
                obs.a_ex,
                obs.v_ex,
                obs.p_or,
                obs.q_or,
                obs.a_or,
                obs.v_or
            ]).flatten()

        load_data["timestep"] = np.repeat(timesteps, episode_data.n_loads)
        load_data["equipment_name"] = np.tile(episode_data.load_names, size).astype(str)
        load_data["equipement_id"] = np.tile(range(episode_data.n_loads), size)

        self.timestamps = sorted(load_data.timestamp.dropna().unique())
        self.timesteps = sorted(load_data.timestep.unique())

        production["timestep"] = np.repeat(timesteps, episode_data.n_prods)
        production["timestamp"] = np.repeat(self.timestamps, episode_data.n_prods)
        production.loc[:, "equipment_name"] = np.tile(episode_data.prod_names, size)
        production.loc[:, "equipement_id"] = np.tile(range(episode_data.n_prods), size)

        rho["time"] = np.repeat(timesteps, n_rho)
        rho["timestamp"] = np.repeat(self.timestamps, n_rho)
        rho["equipment"] = np.tile(range(n_rho), size)

        action_data_table["timestep"] = self.timesteps
        action_data_table["timestamp"] = self.timestamps
        action_data_table["timestep_reward"] = episode_data.rewards[:size]

        load_data["value"] = load_data["value"].astype(float)
        production["value"] = production["value"].astype(float)
        rho["value"] = rho["value"].astype(float)
        return load_data, production, rho, action_data_table, computed_rewards, flow_voltage_line_table

    def get_object_changed(self, vect, list_topo):
        if np.count_nonzero(vect) is 0:
            return None
        for idx, topo_array in enumerate(list_topo):
            if not np.array_equal(topo_array, vect):
                return idx
        # if we havnt found the vect...
        list_topo.append(vect)
        return len(list_topo) - 1

    def get_sub_action(self, act, obs):
        for sub in range(len(obs.sub_info)):
            effect = act.effect_on(substation_id=sub)
            if np.any(effect["change_bus"] is True):
                return self.name_sub[sub]
            if np.any(effect["set_bus"] is 1) or np.any(effect["set_bus"] is -1):
                return self.name_sub[sub]
        return None

    def get_distance_from_obs(self, obs):
        return len(obs.topo_vect) - np.count_nonzero(obs.topo_vect == 1)

    # @jit(forceobj=True)
    def _env_actions_as_df(self, episode_data):
        hazards_size = (len(episode_data.observations) - 1) * episode_data.n_lines
        cols = ["timestep", "timestamp", "line_id", "line_name", "value"]
        hazards = pd.DataFrame(index=range(hazards_size),
                               columns=["value"], dtype=int)
        maintenances = hazards.copy()

        for (time_step, env_act) in tqdm(enumerate(episode_data.env_actions), total=len(episode_data.env_actions)):
            if env_act is None:
                continue

            time_stamp = self.timestamp(episode_data.observations[time_step])

            begin = time_step * episode_data.n_lines
            end = (time_step + 1) * episode_data.n_lines - 1
            hazards.loc[begin:end, "value"] = env_act._hazards.astype(int)

            begin = time_step * episode_data.n_lines
            end = (time_step + 1) * episode_data.n_lines - 1
            maintenances.loc[begin:end, "value"] = env_act._maintenance.astype(int)

        hazards["timestep"] = np.repeat(self.timesteps, episode_data.n_lines)
        maintenances["timestep"] = hazards["timestep"]
        hazards["timestamp"] = np.repeat(self.timestamps, episode_data.n_lines)
        maintenances["timestamp"] = hazards["timestamp"]
        hazards["line_name"] = np.tile(episode_data.line_names, len(self.timesteps))
        maintenances["line_name"] = hazards["line_name"]
        hazards["line_id"] = np.tile(range(episode_data.n_lines), len(self.timesteps))
        maintenances["line_id"] = hazards["line_id"]

        return hazards, maintenances

    def get_prod_types(self):
        types = self.observation_space.gen_type
        ret = {}
        if types is None:
            return ret
        for (idx, name) in enumerate(self.prod_names):
            ret[name] = types[idx]
        return ret

    def decorate(self, episode_data):
        # Add EpisodeData attributes to EpisodeAnalytics
        for attribute in [elem for elem in dir(episode_data) if
                          not (elem.startswith("__") or callable(getattr(episode_data, elem)))]:
            setattr(self, attribute, getattr(episode_data, attribute))


class Test():
    def __init__(self):
        self.foo = 2
        self.bar = 3


if __name__ == "__main__":
    test = Test()
    path_agent = "nodisc_badagent"
    episode = EpisodeData.from_disk(
        "D:/Projects/RTE - Grid2Viz/20200127_data_scripts/20200127_agents_log/" + path_agent, "3_with_hazards")
    print(dir(EpisodeAnalytics(episode)))
