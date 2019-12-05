# grid2viz

This tool provides visualization views to help analyse reinforcement learning of agents in the grid2op challenge.

##Getting started

In order to use this tool, you need to have serialized the RL process of grid2op. The expected file system is :
- root_dir
    - agent_1
        - scenario_1
        - scenario_2
    - agent_2
        - scenario_1
        - scenario_2
        - scenario_3

Each of the scenario_* files have to contain all files given by serialisation of your RL through grid2op.

`//TODO: when the serialisation is freezed, add description of required files`

In the config.ini of this repo, change the `base_dir` option to your root_dir of data, and pick a `scenario` and `agent_ref` to visualize.
Changing this file will require a restart of the server to update.

To launch the server, run the `__main__` in `index.py` :

`$ cd Grid2Viz`

`$ pipenv install`

`$ pipenv run ./src/index.py`
