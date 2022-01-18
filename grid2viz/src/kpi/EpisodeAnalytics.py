# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import datetime as dt
import time

import numpy as np
import pandas as pd
from grid2op.Episode import EpisodeData
from tqdm import tqdm

from . import EpisodeTrace, maintenances, consumption_profiles
from .env_actions import env_actions

import os
import json
from grid2op.Exceptions import Grid2OpException, EnvError, IncorrectNumberOfElements, NonFiniteElement
from grid2op.Action import ActionSpace
from grid2op.Observation import ObservationSpace


# TODO: configure the reward key you want to visualize in agent overview.
# Either as an argument or a dropdown list in the app from which we can choose.
# The reward dataframe should get bigger with all keys available anyway
other_reward_key = "grid_operation_cost"


def compute_losses(obs):
    return (obs.prod_p.sum() - obs.load_p.sum()) / obs.load_p.sum()


class ActionImpacts:
    def __init__(
        self,
        action_line,
        action_subs,
        action_redisp,
        redisp_impact,
        line_name,
        sub_name,
        gen_name,
        action_id,
    ):
        self.action_line = action_line
        self.action_subs = action_subs
        self.action_redisp = action_redisp
        self.redisp_impact = redisp_impact
        self.line_name = line_name
        self.sub_name = sub_name
        self.gen_name = gen_name
        self.action_id = action_id


class EpisodeAnalytics:
    def __init__(self, episode_data, episode_name, agent):
        self.episode_name = episode_name
        self.agent = agent

        self.timesteps = list(range(len(episode_data.actions)))
        print(
            f"Computing DataFrames for scenario {self.episode_name} and agent {self.agent}"
        )
        beg = time.time()
        print("Environment")
        (
            self.load,
            self.production,
            self.rho,
            self.action_data_table,
            self.computed_reward,
            self.flow_and_voltage_line,
            self.target_redispatch,
            self.actual_redispatch,
            self.attacks_data_table,
        ) = self._make_df_from_data(episode_data)
        print("Hazards-Maintenances")
        self.hazards, self.maintenances = self._env_actions_as_df(episode_data)
        print("Computing computation intensive indicators...")
        self.total_overflow_trace = EpisodeTrace.get_total_overflow_trace(
            self, episode_data
        )
        self.usage_rate_trace = EpisodeTrace.get_usage_rate_trace(self)
        self.reward_trace = EpisodeTrace.get_df_rewards_trace(self)
        self.total_overflow_ts = EpisodeTrace.get_total_overflow_ts(self, episode_data)
        self.profile_traces = consumption_profiles.profiles_traces(self)
        self.total_maintenance_duration = maintenances.total_duration_maintenance(self)
        self.nb_hazards = env_actions(self, which="hazards", kind="nb", aggr=True)
        self.nb_maintenances = env_actions(
            self, which="maintenances", kind="nb", aggr=True
        )


        end = time.time()
        print(f"end computing df: {end - beg}")



    @staticmethod
    def timestamp(obs):
        return dt.datetime(
            obs.year, obs.month, obs.day, obs.hour_of_day, obs.minute_of_hour
        )

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
            - target and actual redispatch
            - attacks
            - alarms

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

        load_data = pd.DataFrame(index=range(load_size), columns=["timestamp", "value"])
        load_data.loc[:, "value"] = load_data.loc[:, "value"].astype(float)

        production = pd.DataFrame(index=range(prod_size), columns=["value"])

        rho = pd.DataFrame(index=range(rho_size), columns=["value"])

        cols_loop_action_data_table = [
            "action_line",
            "action_subs",
            "action_redisp",
            "redisp_impact",
            "line_name",
            "sub_name",
            "gen_name",
            "action_id",
            "distance",
            "lines_modified",
            "subs_modified",
            "gens_modified",
            "is_alarm",
            "alarm_zone"
        ]
        action_data_table = pd.DataFrame(
            index=range(size),
            columns=[
                "timestep",
                "timestamp",
                "timestep_reward",
                "action_line",
                "action_subs",
                "action_redisp",
                "redisp_impact",
                "line_name",
                "sub_name",
                "gen_name",
                "action_id",
                "distance",
                "lines_modified",
                "subs_modified",
                "gens_modified",
                "is_alarm",
                "alarm_zone"
            ],
        )

        computed_rewards = pd.DataFrame(
            index=range(size), columns=["timestep", "rewards", "cum_rewards"]
        )
        flow_voltage_cols = pd.MultiIndex.from_product(
            [
                ["or", "ex"],
                ["active", "reactive", "current", "voltage"],
                episode_data.line_names,
            ]
        )
        flow_voltage_line_table = pd.DataFrame(
            index=range(size), columns=flow_voltage_cols
        )

        target_redispatch = pd.DataFrame(
            index=range(size), columns=episode_data.prod_names
        )
        actual_redispatch = pd.DataFrame(
            index=range(size), columns=episode_data.prod_names
        )

        topo_vect = episode_data.observations[0].topo_vect
        if topo_vect.sum() != len(topo_vect):
            raise ValueError("Not all things are on bus 1")

        obs_0 = episode_data.observations[0]

        # True == connected, False == disconnect
        # So that len(line_statuses) - line_statuses.sum() is the distance for lines
        line_statuses = episode_data.observations[0].line_status

        # True == sub has something on bus 2, False == everything on bus 1
        # So that subs_on_bus2.sum() is the distance for subs
        subs_on_bus_2 = np.repeat(False, episode_data.observations[0].n_sub)

        # objs_on_bus_2 will store the id of objects connected to bus 2
        objs_on_bus_2 = {id: [] for id in range(episode_data.observations[0].n_sub)}

        is_alarm=False
        if(("last_alarm" in episode_data.observations[0].__dict__.keys())):
            #if(len(episode_data.observations[1].last_alarm)>=1):
            is_alarm = (episode_data.observations[0].time_since_last_alarm[0]==0)
        # Distance from original topology is then :
        # len(line_statuses) - line_statuses.sum() + subs_on_bus_2.sum()

        gens_modified_ids = []
        actual_redispatch_previous_ts = obs_0.actual_dispatch

        list_actions = []
        for (time_step, (obs, act)) in tqdm(
            enumerate(zip(episode_data.observations[:-1], episode_data.actions)),
            total=size,
        ):
            time_stamp = self.timestamp(obs)
            (
                action_impacts,
                list_actions,
                lines_modified,
                subs_modified,
                gens_modified_names,
                gens_modified_ids,
            ) = self.compute_action_impacts(
                act, list_actions, obs, gens_modified_ids, actual_redispatch_previous_ts
            )

            alarm_zone = []
            if (("last_alarm" in episode_data.observations[1].__dict__.keys())):
                #is_alarm=(obs.time_since_last_alarm[0]==0)#last_alarm[1]
                is_alarm = (obs.time_since_last_alarm[0] == 0) &(len(obs.last_alarm)!=0)
                if is_alarm:
                    alarm_zone=[obs.alarms_area_names[zone_id]
                                for zone_id,zone_value in enumerate(obs.last_alarm) if (int(zone_value)==time_step)]

            actual_redispatch_previous_ts = obs.actual_dispatch

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

            (
                distance,
                line_statuses,
                subs_on_bus_2,
                objs_on_bus_2,
            ) = self.get_distance_from_obs(
                act, line_statuses, subs_on_bus_2, objs_on_bus_2, obs_0
            )

            action_data_table.loc[pos, cols_loop_action_data_table] = [
                action_impacts.action_line,
                action_impacts.action_subs,
                action_impacts.action_redisp,
                action_impacts.redisp_impact,
                action_impacts.line_name,
                action_impacts.sub_name,
                action_impacts.gen_name,
                action_impacts.action_id,
                distance,
                lines_modified,
                subs_modified,
                gens_modified_names,
                is_alarm,
                alarm_zone
            ]

            flow_voltage_line_table.loc[time_step, :] = np.array(
                [
                    obs.p_ex,
                    obs.q_ex,
                    obs.a_ex,
                    obs.v_ex,
                    obs.p_or,
                    obs.q_or,
                    obs.a_or,
                    obs.v_or,
                ]
            ).flatten().astype('float16')

            target_redispatch.loc[time_step, :] = obs.target_dispatch.astype('float32')
            actual_redispatch.loc[time_step, :] = obs.actual_dispatch.astype('float32')

        load_data["timestep"] = np.repeat(timesteps, episode_data.n_loads)
        load_data["equipment_name"] = np.tile(episode_data.load_names, size).astype(str)
        load_data["equipement_id"] = np.tile(range(episode_data.n_loads), size)

        self.timestamps = sorted(load_data.timestamp.dropna().unique())
        self.timesteps = sorted(load_data.timestep.unique())

        production["timestep"] = np.repeat(timesteps, episode_data.n_prods)
        production["timestamp"] = np.repeat(self.timestamps, episode_data.n_prods)
        production.loc[:, "equipment_name"] = np.tile(episode_data.prod_names, size)
        production.loc[:, "equipement_id"] = np.tile(range(episode_data.n_prods), size)

        rho["time"] = np.repeat(timesteps, n_rho).astype('int16')
        rho["timestamp"] = np.repeat(self.timestamps, n_rho)
        rho["equipment"] = np.tile(range(n_rho), size)

        action_data_table["timestep"] = self.timesteps
        action_data_table["timestamp"] = self.timestamps
        action_data_table["timestep_reward"] = episode_data.rewards[:size]

        load_data["value"] = load_data["value"].astype('float32')
        production["value"] = production["value"].astype('float32')
        rho["value"] = rho["value"].astype('float16')

        computed_rewards["timestep"] = self.timestamps
        computed_rewards["rewards"] = episode_data.rewards[:size]

        # TODO: we should give a choice to select different rewards among other rewards
        if episode_data.other_rewards:
            if other_reward_key:
                if other_reward_key in episode_data.other_rewards[0].keys():
                    computed_rewards["rewards"] = [
                        other_reward[other_reward_key]
                        for other_reward in episode_data.other_rewards
                    ]
                    computed_rewards["rewards"] = computed_rewards["rewards"][:size]
        computed_rewards["cum_rewards"] = computed_rewards["rewards"].cumsum(axis=0)

        attacks_data_table = pd.DataFrame(
            index=range(size), columns=["timestep", "timestamp", "attack", "id_lines"]
        )
        attacks_data_table["timestep"] = self.timesteps
        attacks_data_table["timestamp"] = self.timestamps
        for time_step, attack in enumerate(episode_data.attacks):
            (
                n_lines_modified,
                str_lines_modified,
                lines_modified,
            ) = self.get_lines_modifications(attack)
            n_subs_modified, *_ = self.get_subs_modifications(attack)
            is_attacked = n_lines_modified > 0 or n_subs_modified > 0
            attacks_data_table.loc[time_step, "attack"] = is_attacked
            if len(lines_modified) == 0:
                attacks_data_table.loc[time_step, "id_lines"] = ""
            else:
                attacks_data_table.loc[time_step, "id_lines"] = lines_modified[0]

        return (
            load_data,
            production,
            rho,
            action_data_table,
            computed_rewards,
            flow_voltage_line_table,
            target_redispatch,
            actual_redispatch,
            attacks_data_table,
        )

    @staticmethod
    def get_action_id(action, list_actions):
        if not action:
            return None, list_actions
        for idx, act_dict in enumerate(list_actions):
            if action == act_dict:
                return idx, list_actions
        # if we havnt found the vect...
        list_actions.append(action)
        return len(list_actions) - 1, list_actions

    def optimize_memory_footprint(self):
        self.flow_and_voltage_line=self.flow_and_voltage_line.astype('float16')
        self.production.equipment_name=self.production.equipment_name.astype('category')
        self.production.value = self.production.value.astype('float16')
        self.production.timestamp = self.production.timestamp.astype('category')
        self.load.equipment_name = self.load.equipment_name.astype('category')
        self.load.value = self.load.value.astype('float16')
        self.load.timestamp=self.load.timestamp.astype('category')

        self.maintenances.line_name=self.maintenances.line_name.astype('category')
        self.maintenances.timestamp=self.maintenances.timestamp.astype('category')
        self.hazards.line_name = self.hazards.line_name.astype('category')
        self.hazards.timestamp = self.hazards.timestamp.astype('category')



    def get_sub_name(self, act, obs):
        for sub in range(len(obs.sub_info)):
            effect = act.effect_on(substation_id=sub)
            if np.any(effect["change_bus"] is True):
                return self.name_sub[sub]
            if np.any(effect["set_bus"] == 1) or np.any(effect["set_bus"] == -1):
                return self.name_sub[sub]
        return None

    def get_distance_from_obs(
        self, act, line_statuses, subs_on_bus_2, objs_on_bus_2, obs
    ):

        impact_on_objs = act.impact_on_objects()

        # lines reconnetions/disconnections
        line_statuses[
            impact_on_objs["force_line"]["disconnections"]["powerlines"]
        ] = False
        line_statuses[
            impact_on_objs["force_line"]["reconnections"]["powerlines"]
        ] = True
        line_statuses[impact_on_objs["switch_line"]["powerlines"]] = np.invert(
            line_statuses[impact_on_objs["switch_line"]["powerlines"]]
        )

        topo_vect_dict = {
            "load": obs.load_pos_topo_vect,
            "generator": obs.gen_pos_topo_vect,
            "line (extremity)": obs.line_ex_pos_topo_vect,
            "line (origin)": obs.line_or_pos_topo_vect,
        }

        # Bus manipulation
        if impact_on_objs["topology"]["changed"]:
            for modif_type in ["bus_switch", "assigned_bus"]:

                for elem in impact_on_objs["topology"][modif_type]:
                    objs_on_bus_2 = self.update_objs_on_bus(
                        objs_on_bus_2, elem, topo_vect_dict, kind=modif_type
                    )

            for elem in impact_on_objs["topology"]["disconnect_bus"]:
                # Disconnected bus counts as one for the distance
                subs_on_bus_2[elem["substation"]] = True

        subs_on_bus_2 = [
            True if objs_on_2 else False for _, objs_on_2 in objs_on_bus_2.items()
        ]

        distance = len(line_statuses) - line_statuses.sum() + sum(subs_on_bus_2)
        return distance, line_statuses, subs_on_bus_2, objs_on_bus_2

    def update_objs_on_bus(self, objs_on_bus_2, elem, topo_vect_dict, kind):
        for object_type, pos_topo_vect in topo_vect_dict.items():
            if elem["object_type"] == object_type and elem["bus"]:
                if kind == "bus_switch":
                    objs_on_bus_2 = self.update_objs_on_bus_switch(
                        objs_on_bus_2, elem, pos_topo_vect
                    )
                else:
                    objs_on_bus_2 = self.update_objs_on_bus_assign(
                        objs_on_bus_2, elem, pos_topo_vect
                    )
                break
        return objs_on_bus_2

    @staticmethod
    def update_objs_on_bus_switch(objs_on_bus_2, elem, pos_topo_vect):
        if pos_topo_vect[elem["object_id"]] in objs_on_bus_2[elem["substation"]]:
            # elem was on bus 2, remove it from objs_on_bus_2
            objs_on_bus_2[elem["substation"]] = [
                x
                for x in objs_on_bus_2[elem["substation"]]
                if x != pos_topo_vect[elem["object_id"]]
            ]
        else:
            objs_on_bus_2[elem["substation"]].append(pos_topo_vect[elem["object_id"]])
        return objs_on_bus_2

    @staticmethod
    def update_objs_on_bus_assign(objs_on_bus_2, elem, pos_topo_vect):
        if (
            pos_topo_vect[elem["object_id"]] in objs_on_bus_2[elem["substation"]]
            and elem["bus"] == 1
        ):
            # elem was on bus 2, remove it from objs_on_bus_2
            objs_on_bus_2[elem["substation"]] = [
                x
                for x in objs_on_bus_2[elem["substation"]]
                if x != pos_topo_vect[elem["object_id"]]
            ]
        elif (
            pos_topo_vect[elem["object_id"]] not in objs_on_bus_2[elem["substation"]]
            and elem["bus"] == 2
        ):
            objs_on_bus_2[elem["substation"]].append(pos_topo_vect[elem["object_id"]])
        return objs_on_bus_2

    # @jit(forceobj=True)
    def _env_actions_as_df(self, episode_data):
        agent_length = len(
            episode_data.actions
        )  # int(episode_data.meta['nb_timestep_played'])
        hazards_size = agent_length * episode_data.n_lines
        cols = ["timestep", "timestamp", "line_id", "line_name", "value"]
        hazards = pd.DataFrame(index=range(hazards_size), columns=["value"], dtype=int)
        maintenances = hazards.copy()

        for (time_step, env_act) in tqdm(
            enumerate(episode_data.env_actions), total=len(episode_data.env_actions)
        ):
            if env_act is None:
                continue

            time_stamp = self.timestamp(episode_data.observations[time_step])

            begin = time_step * episode_data.n_lines
            end = (time_step + 1) * episode_data.n_lines - 1
            hazards.loc[begin:end, "value"] = env_act._hazards.astype(int)

            begin = time_step * episode_data.n_lines
            end = (time_step + 1) * episode_data.n_lines - 1
            maintenances.loc[begin:end, "value"] = env_act._maintenance.astype(int)

        hazards["timestep"] = np.repeat(range(agent_length), episode_data.n_lines)
        maintenances["timestep"] = hazards["timestep"]
        hazards["timestamp"] = np.repeat(self.timestamps, episode_data.n_lines)
        maintenances["timestamp"] = hazards["timestamp"]
        hazards["line_name"] = np.tile(episode_data.line_names, agent_length)
        maintenances["line_name"] = hazards["line_name"]
        hazards["line_id"] = np.tile(range(episode_data.n_lines), agent_length)
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

    #to be able to save a light pickle file and reload it.
    #saving with reboot lead to pickle errors and reboot is only used in simulation tab
    #better reload the episode data in the simulation tab if reboot is not an attribute of episode_analytics at that stage
    def decorate_light_without_reboot(self, episode_data):
        for attribute in [
                elem
                for elem in dir(episode_data)
                if not (elem.startswith("__") or callable(getattr(episode_data, elem)))
             ]:
            if(attribute=="observations"):
                self.observations=list(episode_data.observations)#make thos objects pickable
            if(attribute=="actions"):
                self.actions=list(episode_data.actions)#make thos objects pickable
            if(attribute in ["prod_names",  "line_names", "load_names", "meta",
                          "rewards"]):
                setattr(self, attribute, getattr(episode_data, attribute))

    def decorate_with_reboot(self, episode_data):
        for attribute in [
                elem
                for elem in dir(episode_data)
                if not (elem.startswith("__") or callable(getattr(episode_data, elem)))
             ]:
            setattr(self, attribute, getattr(episode_data, attribute))
        #add the reboot method
        setattr(self, "reboot", getattr(episode_data, "reboot"))

    def decorate_obs_act_spaces(self,agent_path):

        OBS_SPACE = "dict_observation_space.json"
        ACTION_SPACE = "dict_action_space.json"

        self.observation_space = ObservationSpace.from_dict(
            os.path.join(agent_path, OBS_SPACE))  # need to add action space maybe also, at least for simulation page
        self.action_space = ActionSpace.from_dict(os.path.join(agent_path, ACTION_SPACE))

    def compute_action_impacts(
        self,
        action,
        list_actions,
        observation,
        gens_modified_ids,
        actual_dispatch_previous_ts,
    ):

        (
            n_lines_modified,
            str_lines_modified,
            lines_modified,
        ) = self.get_lines_modifications(action)
        n_subs_modified, str_subs_modified, subs_modified = self.get_subs_modifications(
            action
        )

        (
            n_gens_modified,
            str_gens_modified,
            gens_modified_names,
            gens_modified_ids,
            redisp_volume,
        ) = self.get_gens_modifications(
            action, observation, gens_modified_ids, actual_dispatch_previous_ts
        )

        action_id, list_actions = self.get_action_id(action, list_actions)

        return (
            ActionImpacts(
                action_line=n_lines_modified,
                action_subs=n_subs_modified,
                action_redisp=n_gens_modified,
                redisp_impact=redisp_volume,
                line_name=str_lines_modified,
                sub_name=str_subs_modified,
                gen_name=str_gens_modified,
                action_id=action_id,
            ),
            list_actions,
            lines_modified,
            subs_modified,
            gens_modified_names,
            gens_modified_ids,
        )

    def get_lines_modifications(self, action):
        action_dict = action.as_dict()
        n_lines_modified = 0
        lines_reconnected = []
        lines_disconnected = []
        lines_switched = []
        str_lines_modified = ""
        if "set_line_status" in action_dict:
            n_lines_modified += (
                action_dict["set_line_status"]["nb_connected"]
                + action_dict["set_line_status"]["nb_disconnected"]
            )
            lines_reconnected = [
                *lines_reconnected,
                *[
                    action.name_line[int(line_id)]
                    for line_id in action_dict["set_line_status"]["connected_id"]
                ],
            ]
            if lines_reconnected:
                str_lines_modified += "Reconnect: " + ", ".join(lines_reconnected)
            lines_disconnected = [
                *lines_disconnected,
                *[
                    action.name_line[int(line_id)]
                    for line_id in action_dict["set_line_status"]["disconnected_id"]
                ],
            ]
            if lines_disconnected:
                if str_lines_modified:
                    str_lines_modified += " - "
                str_lines_modified += "Disconnect: " + ", ".join(lines_disconnected)
        if "change_line_status" in action_dict:
            n_lines_modified += action_dict["change_line_status"]["nb_changed"]
            lines_switched = [
                *lines_switched,
                *[
                    action.name_line[int(line_id)]
                    for line_id in action_dict["change_line_status"]["changed_id"]
                ],
            ]
            if lines_switched:
                if str_lines_modified:
                    str_lines_modified += " - "
                str_lines_modified += "Switch: " + ", ".join(lines_switched)

        lines_modified = [*lines_reconnected, *lines_disconnected, *lines_switched]

        return n_lines_modified, str_lines_modified, lines_modified

    def get_subs_modifications(self, action):
        action_dict = action.as_dict()
        n_subs_modified = 0
        subs_modified = []

        if "set_bus_vect" in action_dict:
            n_subs_modified += action_dict["set_bus_vect"]["nb_modif_subs"]
            subs_modified = [
                *subs_modified,
                *[
                    action.name_sub[int(sub_id)]
                    for sub_id in action_dict["set_bus_vect"]["modif_subs_id"]
                ],
            ]
        if "change_bus_vect" in action_dict:
            n_subs_modified += action_dict["change_bus_vect"]["nb_modif_subs"]
            subs_modified = [
                *subs_modified,
                *[
                    action.name_sub[int(sub_id)]
                    for sub_id in action_dict["change_bus_vect"]["modif_subs_id"]
                ],
            ]

        subs_modified_set = set(subs_modified)
        str_subs_modified = " - ".join(subs_modified_set)
        return n_subs_modified, str_subs_modified, subs_modified

    def get_gens_modifications(
        self,
        action,
        observation,
        gens_modified_previous_time_step,
        actual_dispatch_previous_ts,
    ):
        action_dict = action.as_dict()
        n_gens_modified = 0
        gens_modified_ids = []
        gens_modified_names = []
        if "redispatch" in action_dict:
            n_gens_modified = (action_dict["redispatch"] != 0).sum()
            gens_modified_ids = np.where(action_dict["redispatch"] != 0)[0]
            gens_modified_names = action.name_gen[gens_modified_ids]

        str_gens_modified = " - ".join(gens_modified_names)

        volume_redispatched = round(
            np.absolute(
                observation.actual_dispatch[gens_modified_previous_time_step]
                - actual_dispatch_previous_ts[gens_modified_previous_time_step]
            ).sum(),
            2,
        )

        return (
            n_gens_modified,
            str_gens_modified,
            gens_modified_names,
            gens_modified_ids,
            volume_redispatched,
        )

    def get_subs_and_lines_impacted(self, action):
        line_impact, sub_impact = action.get_topological_impact()
        sub_names = action.name_sub[sub_impact]
        line_names = action.name_line[line_impact]
        return sub_names, line_names

    def format_subs_and_lines_impacted(self, sub_names, line_names):
        return self.format_elements_impacted(sub_names), self.format_elements_impacted(
            line_names
        )

    def format_elements_impacted(self, elements):
        if not len(elements):
            elements_formatted = None
        else:
            elements_formatted = " - ".join(elements)
        return elements_formatted

class Test:
    def __init__(self):
        self.foo = 2
        self.bar = 3


if __name__ == "__main__":
    test = Test()
    path_agent = "nodisc_badagent"
    episode = EpisodeData.from_disk(
        "D:/Projects/RTE - Grid2Viz/20200127_data_scripts/20200127_agents_log/"
        + path_agent,
        "3_with_hazards",
    )
    print(dir(EpisodeAnalytics(episode)))
