import grid2op
from grid2op.Agent import TopologyGreedy, DoNothingAgent
from grid2op.Runner import Runner
from grid2op import make
from CustomAgent import RandomRedispatchAgent
from grid2op.Parameters import Parameters

dataset = "rte_case14_realistic"

#use lightsim2grid to go a lot faster if available
try:
    from lightsim2grid.LightSimBackend import LightSimBackend
    backend = LightSimBackend()
except:
    from grid2op.Backend import PandaPowerBackend
    backend = PandaPowerBackend()
    print("You might need to install the LightSimBackend (provisory name) to gain massive speed up")

print('redispatching')
param = Parameters()
#param.init_from_dict({"NO_OVERFLOW_DISCONNECTION": True})

with make(dataset,param=param,backend=backend) as env:
  agent = TopologyGreedy(env.action_space)
  runner = Runner(**env.get_params_for_runner(),
                  agentClass=None,
                  agentInstance=agent)
  #need to be seeded for reproducibility as this takes random redispatching actions
  runner.run(nb_episode=1,
             path_save="grid2viz/data/agents/redispatching-baseline",
             nb_process=1,
             max_iter=100,
             env_seeds=[0],
             agent_seeds=[0],
             pbar=True)
  env.close()

print('do-nothing')
with make(dataset,param=param,backend=backend) as env:
  agent = DoNothingAgent(env.action_space)
  runner = Runner(**env.get_params_for_runner(),
                  agentClass=None,
                  agentInstance=agent)
  runner.run(nb_episode=2,
             path_save="grid2viz/data/agents/do-nothing-baseline",
             nb_process=2,
             max_iter=2000,
             pbar=True)
  env.close()

    
print('greedy')
with make(dataset,param=param,backend=backend) as env:
  agent = TopologyGreedy(env.action_space)
  runner = Runner(**env.get_params_for_runner(),
                  agentClass=None,
                  agentInstance=agent)
  runner.run(nb_episode=2,
             path_save="grid2viz/data/agents/greedy-baseline",
             nb_process=2,
             max_iter=2000,
             pbar=True)
  env.close()
  

