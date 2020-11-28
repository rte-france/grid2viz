import os
import subprocess
import signal
import sys
import time
import pkg_resources
import argparse

CONFIG_FILE_CONTENT = """
# This file have been automatically generated, please do not modify it. 
# You can remove it once done with the application.
[DEFAULT]
agents_dir={agents_dir}
env_dir={env_dir}
n_cores={n_cores}
# This file will be re generated to each call of "python -m grid2viz.main"
"""

ARG_AGENTS_PATH_DESC = (
    "The path where the log of the Agents experiences are stored."
    " (default to None to study the example agents provided with the package)"
)
ARG_ENV_PATH_DESC = (
    "The path where the environment config is stored."
    " (default to None to use the provided default environment)"
)
ARG_PORT_DESC = "The port to serve grid2viz on." " (default to 8050)"
ARG_DEBUG_DESC = "Enable debug mode for developers." " (default to False)"
ARG_N_CORES_DESC = "The number of cores to use for the first loading of the best agents of each scenario"

ARG_CACHE_DESC = "True if you want to build all the cache data for all agents at once before relaunching grid2viz"


def main():
    parser_main = argparse.ArgumentParser(description="Grid2Viz")
    parser_main.add_argument(
        "--agents_path",
        default=None,
        required=False,
        type=str,
        help=ARG_AGENTS_PATH_DESC,
    )
    parser_main.add_argument(
        "--env_path", default=None, required=False, type=str, help=ARG_ENV_PATH_DESC
    )
    parser_main.add_argument(
        "--port", default=8050, required=False, type=int, help=ARG_PORT_DESC
    )
    parser_main.add_argument("--debug", action="store_true", help=ARG_DEBUG_DESC)

    parser_main.add_argument("--n_cores", default=2, type=int, help=ARG_N_CORES_DESC)
    parser_main.add_argument("--cache", default=False, type=bool, help=ARG_CACHE_DESC)

    args = parser_main.parse_args()

    pkg_root_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ["GRID2VIZ_ROOT"] = pkg_root_dir
    config_path = os.path.join(pkg_root_dir, "config.ini")

    if args.agents_path is not None:
        agents_dir = os.path.abspath(args.agents_path)
    else:
        agents_dir = os.path.join(pkg_root_dir, "data", "agents")
        print("Using default agents logs at {}".format(agents_dir))

    if args.env_path is not None:
        env_dir = os.path.abspath(args.env_path)
    else:
        env_dir = os.path.join(pkg_root_dir, "data", "env_conf")
        print("Using default environment at {}".format(env_dir))

    n_cores = args.n_cores

    with open(config_path, "w") as f:
        f.write(
            CONFIG_FILE_CONTENT.format(
                agents_dir=agents_dir, env_dir=env_dir, n_cores=n_cores
            )
        )

    is_makeCache_only = args.cache

    # Inline import to load app only now
    if is_makeCache_only:
        make_cache()
    else:
        from grid2viz.app import app_run

        app_run(args.port, args.debug)


def make_cache():
    from grid2viz.src.manager import (
        scenarios,
        agents,
        make_episode_without_decorate,
        n_cores,
        retrieve_episode_from_disk,
        save_in_ram_cache,
        cache_dir,
    )

    from pathos.multiprocessing import ProcessPool

    if not os.path.exists(cache_dir):
        print("Starting Multiprocessing for reading the best agent of each scenario")

    ##TO DO: tous les agents n'ont pas forcément tourner sur exactement tous les mêmes scenarios
    # Eviter une erreur si un agent n'a pas tourné sur un scenario
    agent_scenario_list = [
        (agent, scenario) for agent in agents for scenario in scenarios
    ]

    agents_data = []
    if n_cores == 1:  # no multiprocess useful for debug if needed
        i = 0
        for agent_scenario in agent_scenario_list:
            agents_data[i] = make_episode_without_decorate(
                agent_scenario[0], agent_scenario[1]
            )
            i += 1
    else:
        pool = ProcessPool(n_cores)
        agents_data = list(
            pool.imap(
                make_episode_without_decorate,
                [agent_scenario[0] for agent_scenario in agent_scenario_list],  # agents
                [agent_scenario[1] for agent_scenario in agent_scenario_list],
            )
        )  # scenarios #we go over all agents and all scenarios for each agent
        pool.close()
        print("Multiprocessing done")

    #####
    # saving data on disk
    i = 0
    for agent_scenario in agent_scenario_list:
        print(i)
        agent = agent_scenario[0]
        episode_name = agent_scenario[1]
        agent_episode = agents_data[i]
        if agent_episode is not None:
            episode_data = retrieve_episode_from_disk(
                agent_episode.episode_name, agent_episode.agent
            )

            agent_episode.decorate(episode_data)
            save_in_ram_cache(
                agent_episode.episode_name, agent_episode.agent, agent_episode
            )
        i += 1


if __name__ == "__main__":
    main()
