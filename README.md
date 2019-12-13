# grid2viz

This tool provides visualization views to help analyse reinforcement learning of agents in the grid2op challenge.

## Installation (Temporary mode)

### Virtualenv creation

Use `pipenv` (recommanded) to build and manage your virtualenv for this project.

If `pipenv` is not installed yet:

`$ pip install pipenv`

Create the virtualenv from the requirements.txt:

```
...$ cd Grid2Viz
.../Grid2Viz$ pipenv install
```


### Grid2Op installation

In order to use the not (yet) integrated `grid2op` version, you have to manually install it into your virtualenv.

Activate the virtualenv:

`.../Grid2Viz$ pipenv shell`

cd to the forked version of `grid2op` and run : 

`(venvname)/.../grid2op$ python setup.py install`

## Getting started

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

To launch the server :
- Set the environment variable `FLASK_APP=/paht/to/src/index.py`
- In the grid2viz folder, run `pipenv run ./src/index.py`'
