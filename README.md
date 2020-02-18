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
In order to add a new agent to the app, you will have to add the agent's folder to this root_dir
For the update process of this folder chain, see the section `Caching` (in particular, when you want to overwrite the current
agents in root_dir with new versions with the same names)

In the config.ini of this repo:
 - change the `base_dir` option to your root_dir of data.
 - change the `env_conf_folder` option to the directory that contains the following two files :
    - prod_share.csv : The csv file that links production equipments to their type
    - coords.csv : The csv file that lists the coordinates of nodes in the network

Changing this config.ini file will require a restart of the server to update.

To launch the server :
- Set the environment variable `export FLASK_APP=/path/to/src/index.py`
- In the grid2viz folder, run `pipenv shell`'
- Run `flask run`

##  Caching

The cache system allows you to only compute long calculations of the app once per agent/scenario.
The app will create a folder `_cache` in the `base_dir` of the config.ini which will contain these long calculations serialized.

If you add a new folder in your `base_dir` (either an agent, or a scenario) you will have to restart the server so the app
reads the folder tree again.

**_WARNING_** : If you overwrite the agents while they were already cached, you will have to manually reset the cache so the app
knows to compute everything again with the updated data. To do so, you just need to delete the `_cache` folder.