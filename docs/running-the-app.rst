*****************************************
Running the application and Configuration
*****************************************

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
For the update process of this folder chain, see the section `Caching` (in particular, when you want to overwrite the current agents in root_dir with new versions with the same names)

The grid2viz commandline tool allows to start the server and provide all the necessary information. The help function of the tool can be found below.

.. code-block:: RST

    usage: grid2viz [-h] [--agents_path AGENTS_PATH] [--env_path ENV_PATH] [--port PORT] [--debug] [--n_cores N_CORES] [--cache CACHE] [--warm-start WARM_START]
                    [--config-path CONFIG_PATH] [--activate-beta ACTIVATE_BETA]

    Grid2Viz

    optional arguments:
      -h, --help            show this help message and exit
      --agents_path AGENTS_PATH
                            The path where the log of the Agents experiences are stored. (default to None to study the example agents provided with the package)
      --env_path ENV_PATH   The path where the environment config is stored. (default to None to use the provided default environment)
      --port PORT           The port to serve grid2viz on. (default to 8050)
      --debug               Enable debug mode for developers. (default to False)
      --n_cores N_CORES     The number of cores to use for the first loading of the best agents of each scenario
      --cache               Enable the building of all the cache data for all agents at once before relaunching grid2viz. (default to False)
      --warm-start          If True, the application is warm started based on the parameters defined in the WARMSTART section of the config.ini file. (default to False)
      --config-path CONFIG_PATH
                            Path to the configuration file config.ini.
      --activate-beta       Enable beta features. (default to False)


For example, to run the server on port 8000 with the default agents provided in the :doc: `Starting-Kit<starting-kit>`: 

.. code-block:: RST

    source venv_grid2viz/bin/activate
    grid2viz --port 8000

-------------
Configuration
-------------

The --config-path argument allows to provide a configuration ini file to pass some options as describe bellow.

.. code-block:: RST

    [DEFAULT]
    agents_dir= # Same as the --agents_path command line argument
    env_dir=# Same as the --env_path command line argument

    [WARMSTART] # Section used to warm start the application form a specfici view
    scenario= # Name of the scenario to be loaded
    agent_ref= # Name of the reference agent to be loaded
    agent_study= # Name of the study agent to be loaded
    page= # End-Point of the view to be loaded (episodes, overview, macro, micro, simulation)
    time_step= # Time step to be loaded



**The command line arguments have precedence over the config file.**

**WARNING:** Due to the caching operation the first run can take a while. All the agents present in the configuration files
will be computed and then registered in cache. Depending on your agents it could take between 5 to 15min. You can follow the progress in the console.*
