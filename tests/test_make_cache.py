import os
import pathlib
import shutil
import subprocess
import unittest


class TestMakeCache(unittest.TestCase):
    def setUp(self):
        self.agent_path = os.path.join(
            pathlib.Path(__file__).parent.absolute(), "data", "agents_to_cache"
        )
        if os.path.isdir(os.path.join(self.agent_path, "_cache")):
            shutil.rmtree(os.path.join(self.agent_path, "_cache"))

    def test_make_cache(self):
        print(self.agent_path)
        cmd = ["grid2viz", "--agents_path", self.agent_path, "--cache"]
        rv = subprocess.run(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE#, shell=True
        )
        self.assertEqual(rv.returncode, 0)
