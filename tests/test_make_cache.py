import os
import pathlib
import shutil
import subprocess
import unittest
from grid2viz.src.manager import make_cache,scenarios,agents,n_cores,cache_dir,get_from_fs_cache


# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

agents_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "data", "agents")

#config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")

class TestMakeCache(unittest.TestCase):
    def setUp(self):
        self.agent_path = agents_path
        self.agent="greedy-baseline"
        for scenario in ["000","001"]:
            cache_file_path=os.path.join(self.agent_path, "_cache", scenario,self.agent+".dill")
            if os.path.exists(cache_file_path):
                os.remove(cache_file_path)
            if os.path.exists(cache_file_path+".bz"):
                os.remove(cache_file_path+".bz")
        #if os.path.isdir(os.path.join(self.agent_path, "_cache")):
        #    shutil.rmtree(os.path.join(self.agent_path, "_cache"))

    def test_make_cache(self):
        print(self.agent_path)
        try:
            make_cache(scenarios,agents,n_cores,cache_dir,agent_selection=[self.agent])#to run the test quicker
        except Exception as e:
            print(e)
            assert(False)

        #try to load one then
        #don't try it on circleci as we might not have had the rights to write the dill.file
        #try:
        #    get_from_fs_cache(scenarios.pop(), self.agent)
        #except Exception as e:
        #    print(e)
        #    assert(False)
#
        #calling grid2viz cli does not work when testing on circle ci
        #cmd = ["grid2viz", "--agents_path", self.agent_path, "--cache"]
        #rv=os.system("grid2viz --agents_path "+self.agent_path+" --cache")
        #rv = subprocess.run(
        #    cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE#, shell=True
        #)
        #self.assertEqual(rv.returncode, 0)
        #self.assertEqual(rv, 0)

