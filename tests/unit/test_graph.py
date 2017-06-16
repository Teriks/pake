import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake.graph


class GraphTest(unittest.TestCase):
    def test_detect_cycle(self):

        graph = pake.graph.Graph()

        edge1 = pake.graph.Graph()
        edge2 = pake.graph.Graph()
        edge3 = pake.graph.Graph()
        edge4 = pake.graph.Graph()
        edge5 = pake.graph.Graph()

        graph.add_edge(edge1)
        graph.add_edge(edge2)
        graph.add_edge(edge3)

        edge3.add_edge(edge4)
        edge4.add_edge(edge5)
        edge5.add_edge(graph)

        with self.assertRaises(pake.graph.CyclicGraphException):
            list(graph.topological_sort())

        graph = pake.graph.Graph()

        edge1 = pake.graph.Graph()
        edge2 = pake.graph.Graph()
        edge3 = pake.graph.Graph()
        edge4 = pake.graph.Graph()
        edge5 = pake.graph.Graph()

        graph.add_edge(edge1)
        graph.add_edge(edge2)
        graph.add_edge(edge3)

        edge3.add_edge(edge4)
        edge4.add_edge(edge5)

        try:
            # force generator to run
            list(graph.topological_sort())
        except pake.graph.CyclicDependencyException:
            self.fail('Topological sort threw CyclicDependencyException on non cyclic graph')

    def test_sort(self):
        # Two dependencies of the same node can come in any order.

        a = pake.graph.Graph()
        b = pake.graph.Graph()
        c = pake.graph.Graph()
        d = pake.graph.Graph()
        e = pake.graph.Graph()

        a.add_edge(b)
        b.add_edge(c)

        # any order
        c.add_edge(d)
        c.add_edge(e)

        expect = [e, d, c, b, a]
        or_expect = [d, e, c, b, a]

        for idx, node in enumerate(a.topological_sort()):
            if expect[idx] is not node:
                expect = False
                break

        for idx, node in enumerate(a.topological_sort()):
            if or_expect[idx] is not node:
                or_expect = False
                break

        if not expect and not or_expect:
            self.fail("Topological sort of simple graph is out of order.")


if __name__ == 'main':
    unittest.main()
