import unittest

import sys
import os

sys.path.insert(1,
                os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

import pake.graph


class GraphTest(unittest.TestCase):
    def test_detect_cycle(self):
        graph = {1: [3], 3: [4, 2], 4: [2], 2: [1]}
        self.assertTrue(pake.graph.check_cyclic(graph))

        with self.assertRaises(pake.graph.CyclicDependencyException):
            # force generator to run
            list(pake.graph.topological_sort(graph))

        graph = {0: [1, 2, 3], 1: [], 2: [3], 3: [], 5: []}
        self.assertFalse(pake.graph.check_cyclic(graph))

        try:
            # force generator to run
            list(pake.graph.topological_sort(graph))
        except pake.graph.CyclicDependencyException:
            self.fail(
                'pake.graph.topological sort threw CyclicDependencyException on non cyclic graph')

        graph = {0: [1, 2], 2: [3], 3: [4], 4: [5, 6], 5: [], 1: [], 6: [0]}
        self.assertTrue(pake.graph.check_cyclic(graph))

        with self.assertRaises(pake.graph.CyclicDependencyException):
            # force generator to run
            list(pake.graph.topological_sort(graph))

    def test_sort(self):
        # Singular dependency for each node is the only way
        # to get a sorted output that is deterministic
        #
        # Two dependencies of the same node could come in any order.
        #
        graph = {"A": ["B"], "B": ["C"], "C": ["D"], "D": []}
        expect = ["D", "C", "B", "A"]
        for idx, node in enumerate(pake.graph.topological_sort(graph)):
            if expect[idx] != node[0]:
                self.fail("Topological sort of simple graph is out of order.")


if __name__ == 'main':
    unittest.main()
