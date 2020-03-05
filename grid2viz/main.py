import os
import subprocess
import signal
import sys
import time

import pkg_resources
import argparse
PARSER_MAIN = argparse.ArgumentParser(description='Launch the Grid2Viz application to study your agent.')
PARSER_MAIN.add_argument('--path', default=None,
                         help='The path where the log of the experience are stored (default None to study the example'
                         'data provided in the package)')

# cur_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

cur_dir = os.path.join(pkg_resources.resource_filename(__name__, ""))

my_env = os.environ.copy()

my_env["FLASK_APP"] = os.path.join(cur_dir, "index.py")

my_env["GRID2VIZ_ROOT"] = cur_dir

my_cmd = "flask run".split(" ")

config_file = \
"""
# This file have been automatically generated, please do not modify it. You can remove it once done with the application.
[DEFAULT]
base_dir = {base_dir}
env_conf_folder = 
# This file will be re generated to each call of "python -m grid2viz.main"
"""


def main(args):
    with open("config.ini", "w") as f:
        if args.path is not None:
            f.write(config_file.format(base_dir=os.path.abspath(args.path)))
        else:
            print("INFO Using the default provided environment")
            f.write(config_file.format(base_dir=""))
    proc = subprocess.Popen(my_cmd, env=my_env)
    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            time.sleep(1)
            print('You pressed Ctrl+C! Shutting down Grid2Viz!')
            proc.send_signal(signal.SIGINT)
            sys.exit(0)


if __name__ == "__main__":
    args = PARSER_MAIN.parse_args()
    main(args)


