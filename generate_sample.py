import grid2op
from grid2op.Agent import TopologyGreedy, DoNothingAgent
from grid2op.Runner import Runner
from grid2op import make

dataset = "rte_case14_realistic"

with make(dataset) as env:
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

with make(dataset) as env:
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
