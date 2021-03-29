from grid2op.MakeEnv import make
from grid2op.Parameters import Parameters

from grid2viz.src.manager import env_path


p = Parameters()
p.NO_OVERFLOW_DISCONNECTION = False
env = make(
    env_path,
    test=True,
    param=p,
)
env.seed(0)
params_for_runner = env.get_params_for_runner()
params_to_fetch = ["init_grid_path"]
params_for_reboot = {
    key: value for key, value in params_for_runner.items() if key in params_to_fetch
}
params_for_reboot["parameters"] = p
