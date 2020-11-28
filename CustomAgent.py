import grid2op

from grid2op.Agent import BaseAgent

from functools import partial
import itertools
from pprint import pprint
import numpy as np


class RandomRedispatchAgent(BaseAgent):
    def __init__(
        self, action_space, env, n_gens_to_Redispatch=2, redispatching_increment=1
    ):
        """
        Initialize agent
        :param action_space: the Grid2Op action space
        :param n_gens_to_Redispatch: the maximum number of dispatchable generators to play with
        :param redispatching_increment: the redispatching MW value to play with (both Plus or Minus)
        """
        BaseAgent.__init__(self, action_space)
        self.desired_actions = []

        # we create a dictionnary of redispatching actions we want to play with
        GensToRedipsatch = [
            i for i in range(len(env.gen_redispatchable)) if env.gen_redispatchable[i]
        ]
        if len(GensToRedipsatch) > n_gens_to_Redispatch:
            GensToRedipsatch = GensToRedipsatch[0:n_gens_to_Redispatch]

        # action dic will have 2 actions par generator (increase or decrease by the increment) + do nothing
        self.desired_actions.append(self.action_space({}))  # do_nothing action

        for i in GensToRedipsatch:

            # redispatching decreasing the production by the increment
            act1 = self.action_space({"redispatch": [(i, -redispatching_increment)]})
            self.desired_actions.append(act1)

            # redispatching increasing the production by the increment
            act2 = self.action_space({"redispatch": [(i, +redispatching_increment)]})
            self.desired_actions.append(act2)

    def act(self, observation, reward, done=False):
        """
        By definition, all "greedy" agents are acting the same way. The only thing that can differentiate multiple
        agents is the actions that are tested.
        These actions are defined in the method :func:`._get_tested_action`. This :func:`.act` method implements the
        greedy logic: take the actions that maximizes the instantaneous reward on the simulated action.
        Parameters
        ----------
        observation: :class:`grid2op.Observation.Observation`
            The current observation of the :class:`grid2op.Environment.Environment`
        reward: ``float``
            The current reward. This is the reward obtained by the previous action
        done: ``bool``
            Whether the episode has ended or not. Used to maintain gym compatibility
        Returns
        -------
        res: :class:`grid2op.Action.Action`
            The action chosen by the bot / controller / agent.
        """

        return self.space_prng.choice(self.desired_actions)


class MultipleTopologyAgent(BaseAgent):
    def __init__(
        self,
        action_space,
        observation_space,
        n_sub_to_play=2,
        n_line_to_play=2,
        max_simultaneous_sub_actions=2,
        max_simultaneous_line_actions=2,
    ):
        super().__init__(action_space)
        self.observation_space = observation_space
        self.n_sub_to_play = n_sub_to_play
        self.n_line_to_play = n_line_to_play
        self.max_simultaneous_sub_actions = max_simultaneous_sub_actions
        self.max_simultaneous_line_actions = max_simultaneous_line_actions
        self._is_built = False

        """
        Initialize agent
        :param action_space: the Grid2Op action space
        :param observation_space: the Grid2Op observatio space 
        :param n_sub_to_play: the number of substations to play on (the largest ones)
        :param n_line_to_play: the number of lines to play on
        :param max_simultaneous_sub_actions: the max number of substations to play on for a simultaneous combined action
        :param max_simultaneous_line_actions: the max number of lines to play on for a simultaneous combined action
        """

    def reset(self, obs):
        if not self._is_built:
            self._build()

    def _build(self):
        self.line_actions_dic = self.unitary_line_actions()
        self.sub_actions_dic = self.unitary_sub_actions()

        # 1) Lines actions
        ## Get lines ids combinations
        combined_lines = self.combined_action_keys(
            action_dic=self.line_actions_dic, depth=self.max_simultaneous_sub_actions
        )
        print("--- Lines combinations ---")
        print(combined_lines)
        print("--------------------------")

        ## Build combined lines acitons
        self.desired_line_actions = []
        for line_comb in combined_lines:
            line_act = self.merge_combined_actions(self.line_actions_dic, line_comb)
            self.desired_line_actions.append(line_act)
        ## Add lines do nothing action
        self.desired_line_actions.append(self.action_space({}))
        print("--- Lines combined actions ---")
        for line_act in self.desired_line_actions:
            print(line_act)
        print("------------------------------")

        # 2) Get substations ids combinations
        combined_subs = self.combined_action_keys(
            action_dic=self.sub_actions_dic, depth=self.max_simultaneous_sub_actions
        )
        print("--- Subs combinations ---")
        print(combined_subs)
        print("-------------------------")
        ## Build combined substations actions
        self.desired_sub_actions = []
        for sub_comb in combined_subs:
            sub_comb_acts = self.merge_combined_actions_subs(
                self.sub_actions_dic, sub_comb
            )
            self.desired_sub_actions += sub_comb_acts
        ## Add substations do_nothing action
        self.desired_sub_actions.append(self.action_space({}))
        print("--- Subs combined actions ---")
        for sub_act in self.desired_sub_actions:
            print(sub_act)
        print("-----------------------------")

        # Set flag to prevent rebuild
        self._is_built = True

    def act(self, observation, reward, done=False):
        # Create Grid2op empty Action
        act = self.action_space({})
        # Merge with a combined line action
        act += self.space_prng.choice(self.desired_line_actions)
        # Merge with a combined substation action
        act += self.space_prng.choice(self.desired_sub_actions)

        print("---- Playing -----")
        print(act)
        print("------------------")

        # Return resulting action
        return act

    def unitary_line_actions(self):
        lineIds = [i for i in range(self.observation_space.n_line)]
        desired_line_actions_dic = {}
        print(self.n_line_to_play)
        lines_to_switch = list(self.space_prng.choice(lineIds, self.n_line_to_play))

        # desired_line_actions_dic['do-nothing']={}
        desired_line_actions = []
        for line_id in lines_to_switch:
            action_name = {"change_line_status": [line_id]}
            desired_line_actions_dic[line_id] = action_name

        return desired_line_actions_dic

    def unitary_sub_actions(self):

        n_subs = self.observation_space.n_sub
        SubIds = [i for i in range(n_subs)]
        desired_sub_actions_dic = {}

        # take subs with most elements

        ranked = np.argsort(np.array(self.observation_space.sub_info))
        largest_indices = ranked[::-1][:n_subs]

        sub_to_switch = largest_indices[0 : self.n_sub_to_play]

        # desired_line_actions_dic['do-nothing']={}
        desired_sub_actions = []
        for sub_id in sub_to_switch:
            n_elements = self.observation_space.sub_info[sub_id]

            target_topology_1 = np.ones(n_elements)
            action_def_1 = {
                "set_bus": {"substations_id": [(sub_id, target_topology_1)]}
            }

            target_topology_2 = np.ones(n_elements)
            target_topology_2[[2 * i for i in range(int(np.round(n_elements / 2)))]] = 2
            action_def_2 = {
                "set_bus": {"substations_id": [(sub_id, target_topology_2)]}
            }

            desired_sub_actions_dic[sub_id] = [action_def_1, action_def_2]

        return desired_sub_actions_dic

    def combined_action_keys(self, action_dic, depth):
        comb = []
        for i in range(1, depth + 1):
            comb += list(itertools.combinations(action_dic.keys(), i))
        return comb

    def merge_combined_actions(self, action_dict, actions_keys):
        act = self.action_space({})

        for action_key in actions_keys:
            action_def = action_dict[action_key]
            tmp = self.action_space(action_def)
            act += tmp

        return act

    def merge_combined_actions_subs(self, sub_actions_dict, subs_keys):
        acts = []

        sub_acts_def = []
        for k in subs_keys:
            sub_acts_def.append(sub_actions_dict[k])

        for sub_act_comb_def in itertools.product(*sub_acts_def):
            act = self.action_space({})
            for a_def in sub_act_comb_def:
                act += self.action_space(a_def)
            acts.append(act)

        return acts
