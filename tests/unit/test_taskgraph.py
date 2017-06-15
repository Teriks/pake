import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))


import pake
import pake.program

class TaskGraphTest(unittest.TestSuite):

    def test_taskgraph_init(self):

        with self.assertRaises(ValueError):
            # Beause name is None
            _ = pake.TaskGraph(None, lambda: '_')

        with self.assertRaises(ValueError):
            # Because func is None
            _ = pake.TaskGraph('name', None)

        with self.assertRaises(ValueError):
            # Because func is not callable
            _ = pake.TaskGraph('name', 1)