import os
import pathlib
import subprocess
import unittest


class TestMakeCache(unittest.TestCase):
    def setUp(self):
        self.agent_path = os.path.join(
            pathlib.Path(__file__).parent.absolute(),
            'data', 'agents')

    def test_make_cache(self):
        cmd = [
            'grid2viz',
            '--agents_path', self.agent_path,
            '--cache', 'True'
        ]
        rv = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.assertEqual(rv.returncode, 0)
