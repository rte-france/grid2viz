import os
import subprocess
import signal
import sys
import time


cur_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))

my_env = os.environ.copy()

my_env["FLASK_APP"] = os.path.join(cur_dir, "src", "index.py")

my_cmd = "flask run".split(" ")

proc = subprocess.Popen(
    my_cmd, env=my_env)

while True: 
    try:
        time.sleep(2)
    except KeyboardInterrupt:
        time.sleep(1)
        print('You pressed Ctrl+C! Shutting down Grid2Viz!')
        proc.send_signal(signal.SIGINT)
        sys.exit(0)
