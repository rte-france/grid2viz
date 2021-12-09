# Copyright (C) 2021, RTE (http://www.rte-france.com/)
# See AUTHORS.txt
# SPDX-License-Identifier: MPL-2.0

import os
import grid2op
from grid2op.operator_attention import LinearAttentionBudget
from grid2op.Agent import TopologyGreedy, DoNothingAgent
from grid2op.Runner import Runner
from grid2op import make,make_from_dataset_path
from CustomAgent import RandomRedispatchAgent, MultipleTopologyAgent, DoNothing_Attention_Agent
from grid2op.Parameters import Parameters

dataset_path = "tests/data/rte_case14_realistic"#"rte_case14_realistic"

# use lightsim2grid to go a lot faster if available
try:
    from lightsim2grid.LightSimBackend import LightSimBackend

    backend = LightSimBackend()
except:
    from grid2op.Backend import PandaPowerBackend

    backend = PandaPowerBackend()
    print(
        "You might need to install the LightSimBackend (provisory name) to gain massive speed up"
    )
#

params = Parameters()
params.init_from_dict({"NO_OVERFLOW_DISCONNECTION": True})
params.MAX_SUB_CHANGED = 999  # to have unlimited sub actions at a timestep
params.MAX_LINE_STATUS_CHANGED = 999  # to have unlimited line actions at a timestep


print("MultiTopology")
path_save = "grid2viz/data/agents/multiTopology-baseline"
os.makedirs(path_save, exist_ok=True)

env=make_from_dataset_path(dataset_path, param=params, backend=backend, has_attention_budget=True,
                       attention_budget_class=LinearAttentionBudget,
                       kwargs_attention_budget={"max_budget": 3.,
                                                "budget_per_ts": 1. / (12. * 16),
                                                "alarm_cost": 1.,
                                                "init_budget": 2.})
#with make(dataset, param=params, backend=backend) as env:
agent = MultipleTopologyAgent(env.action_space, env.observation_space)
runner = Runner(**env.get_params_for_runner(), agentClass=None, agentInstance=agent)
# need to be seeded for reproducibility as this takes random redispatching actions
runner.run(
    nb_episode=1,
    path_save="grid2viz/data/agents/multiTopology-baseline",
    nb_process=1,
    max_iter=30,
    env_seeds=[0],
    agent_seeds=[0],
    pbar=True,
)
#env.close() #problem closing for now: says already closed


print("redispatching")

#with make(dataset, param=params, backend=backend2) as env2:
agent = RandomRedispatchAgent(env.action_space, env)
runner = Runner(**env.get_params_for_runner(), agentClass=None, agentInstance=agent)
# need to be seeded for reproducibility as this takes random redispatching actions
runner.run(
    nb_episode=1,
    path_save="grid2viz/data/agents/redispatching-baseline",
    nb_process=1,
    max_iter=100,
    env_seeds=[0],
    agent_seeds=[0],
    pbar=True,
)
    #env2.close()

print("do-nothing")
#with make(dataset, param=params, backend=backend) as env:
agent = DoNothingAgent(env.action_space)
runner = Runner(**env.get_params_for_runner(), agentClass=None, agentInstance=agent)
runner.run(
    nb_episode=2,
    path_save="grid2viz/data/agents/do-nothing-baseline",
    nb_process=1,
    max_iter=2000,
    pbar=True,
)
    #env.close()


print("greedy")
#with make(dataset, param=params, backend=backend) as env:
agent = TopologyGreedy(env.action_space)
runner = Runner(**env.get_params_for_runner(), agentClass=None, agentInstance=agent)
runner.run(
    nb_episode=2,
    path_save="grid2viz/data/agents/greedy-baseline",
    nb_process=1,
    max_iter=2000,
    pbar=True,
)

print("alarm-agent")
agent = DoNothing_Attention_Agent(env)
runner = Runner(
    **env.get_params_for_runner(), agentClass=None, agentInstance=agent
)
# need to be seeded for reproducibility as this takes random redispatching actions
runner.run(
    nb_episode=1,
    path_save="grid2viz/data/agents/alarm-baseline",
    nb_process=1,
    max_iter=10,
    env_seeds=[0],
    agent_seeds=[0],
    pbar=True,
)

env.close()


