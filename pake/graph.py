# Copyright (c) 2017, Teriks
# All rights reserved.
#
# pake is distributed under the following BSD 3-Clause License
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


__all__ = ['CyclicGraphException', 'Graph']


class CyclicGraphException(Exception):
    """
    Thrown if a graph is determined to be cyclic upon running topological sort on it.
    """

    def __init__(self, *args):
        super(Exception, self).__init__(*args)


class Graph:
    """
    Represents a node in a directed graph.
    """

    def __init__(self):
        self._edges = set()

    def add_edge(self, edge):
        """
        Add an edge to the graph.
        
        :param edge: The edge to add (another :py:class:`pake.graph.Graph` object)
        """
        self._edges.add(edge)

    def remove_edge(self, edge):
        """
        Remove an edge from the graph by reference.
        
        :param edge: Reference to a :py:class:`pake.graph.Graph` object.
        """
        self._edges.remove(edge)

    @property
    def edges(self):
        """
        Retrieve a set of edges from this graph node.
        
        :return: A set() of adjacent nodes.
        """
        return self._edges

    @staticmethod
    def _topological_sort(vertex, visited):
        visited.add(vertex)

        for i in vertex.edges:
            if i not in visited:
                yield from Graph._topological_sort(i, visited)
            else:
                raise CyclicGraphException(
                    'cycle detected, node: "{}" already seen.'.format(i)
                )

        yield vertex

    def topological_sort(self):
        """
        Return a generator object that runs topological sort as it is iterated over.
        
        :raises: :py:class:`pake.CyclicGraphException` if a cycle is found in the graph.
        :return: A generator that produces :py:class:`pake.graph.Graph` nodes.
        """

        visited = set()

        for i in self.edges:
            if i not in visited:
                yield from self._topological_sort(i, visited)
            else:
                raise CyclicGraphException(
                    'Cyclic graph detected, node: "{}" already seen.'.format(i)
                )

        yield self
