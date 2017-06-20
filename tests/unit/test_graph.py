import sys
import unittest

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(1, os.path.abspath(
    os.path.join(script_dir, os.path.join('..', '..'))))

import pake.graph


class GraphTest(unittest.TestCase):
    def test_cycle(self):
        # Tasks which have been visited are ignored

        A = pake.graph.Graph()

        self.assertListEqual([A], list(A.topological_sort()))

        B = pake.graph.Graph()

        A.add_edge(B)
        B.add_edge(A)

        # A -> B -> (A ignored)
        self.assertListEqual([A, B], list(B.topological_sort()),
                             msg='Topological sort short cyclic graph, unexpected result.')

        A = pake.graph.Graph()
        B = pake.graph.Graph()
        C = pake.graph.Graph()
        D = pake.graph.Graph()

        # A -> B -> C -> D -> (A ignored)
        A.add_edge(B)
        B.add_edge(C)
        C.add_edge(D)
        D.add_edge(A)

        self.assertListEqual([D, C, B, A], list(A.topological_sort()),
                             msg='Topological sort long cyclic graph, unexpected result.')

        # Test mutual dependencies, both of A's
        # dependencies (D and B) depend on C

        A = pake.graph.Graph()
        B = pake.graph.Graph()
        C = pake.graph.Graph()
        D = pake.graph.Graph()

        A.add_edge(D)
        A.add_edge(B)
        B.add_edge(C)
        D.add_edge(C)

        result = list(A.topological_sort())

        # The order of D and B are random
        # C needs to build first, then (B, D) or (D, B) then A can build

        self.assertTrue(result == [C, B, D, A] or result == [C, D, B, A],
                        msg='Topological sort mutual dependency graph, unexpected result.')

        # Test another form of mutual dependency
        # A depends B and C,  B depends C

        # order of build should be C, B, A

        A = pake.graph.Graph()
        B = pake.graph.Graph()
        C = pake.graph.Graph()

        A.add_edge(B)
        A.add_edge(C)
        B.add_edge(C)

        self.assertListEqual([C, B, A], list(A.topological_sort()),
                             msg='Topological sort mutual dependency graph, unexpected result.')

        # Duplicate dependencies in a task should just be ignored

        A = pake.graph.Graph()
        B = pake.graph.Graph()
        A.add_edge(B)
        A.add_edge(B)

        self.assertListEqual([B, A], list(A.topological_sort()),
                             msg='Topological sort duplicate dependencies, unexpected result.')

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

        result = list(a.topological_sort())

        self.assertTrue(result == expect or result == or_expect,
                        msg='Topological sort on graph, unexpected result.')


if __name__ == 'main':
    unittest.main()
