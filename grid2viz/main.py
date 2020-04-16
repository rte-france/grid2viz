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
# This file will be re generated to each call of "python -m grid2viz.main"
"""

ARG_AGENTS_PATH_DESC = 'The path where the log of the Agents experiences are stored.' \
                       ' (default None to study the example agents provided with the package)'
ARG_ENV_PATH_DESC = 'The path where the environment config is stored.' \
                    ' (default None to use the provided default environment'
ARG_PORT_DESC = 'The port to serve grid2viz on'
ARG_DEBUG_DESC = 'Enable debug mode (for developers)'

def main():
    parser_main = argparse.ArgumentParser(description='Grid2Viz')
    parser_main.add_argument('--agents_path', default=None,
                             required=False, type=str,
                             help=ARG_AGENTS_PATH_DESC)
    parser_main.add_argument('--env_path', default=None,
                             required=False, type=str,
                             help=ARG_ENV_PATH_DESC)
    parser_main.add_argument('--port', default=8050,
                             required=False, type=int,
                             help=ARG_PORT_DESC)
    parser_main.add_argument('--debug', action='store_true',
                             help=ARG_DEBUG_DESC)

    args = parser_main.parse_args()

    pkg_root_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ["GRID2VIZ_ROOT"] = pkg_root_dir
    config_path = os.path.join(pkg_root_dir, "config.ini")

    if args.agents_path is not None:
        agents_dir = os.path.abspath(args.agents_path)
    else:            
        agents_dir = os.path.join(pkg_root_dir, "data", "agents")
        print ("Using default agents logs at {}".format(agents_dir))

    if args.env_path is not None:
        env_dir = os.path.abspath(args.env_path)
    else:
        env_dir = os.path.join(pkg_root_dir, "data", "env_conf")
        print ("Using default environment at {}".format(env_dir))

    with open(config_path, "w") as f:    
        f.write(CONFIG_FILE_CONTENT.format(agents_dir = agents_dir, env_dir = env_dir))

    # Inline import to load app only now
    from grid2viz.app import app_run
    app_run(args.port, args.debug)

if __name__ == "__main__":
    main()


