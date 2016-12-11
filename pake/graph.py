# Copyright (c) 2016, Teriks
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

import pake.exception


class CyclicDependencyException(pake.exception.PakeException):
    """Raised upon detecting a cyclic dependency in a dependency graph."""
    pass


def _get_edges_or_empty(graph, vertex, get_edges):
    if vertex in graph:
        return get_edges(graph[vertex])
    else:
        return []


def check_cyclic(graph, get_edges=None):
    """Determine if a directed graph is cyclic, graphs are given in the form {node : [edge1, edge2], ...}

    :param graph: A graph in the form {node : [edge1, edge2], ...}, see get_edges parameter for caveats
    :type graph: dict

    :param get_edges:  If your edges container is not an iterable type, this should be a function
                       that returns an iterable over a series of edges (References to other nodes in the graph)

    :type get_edges: func

    :return: True if the graph contains a cycle, False otherwise.
    """

    if get_edges is None:
        def get_edges(t): return t

    path = set()

    def visit(node):
        path.add(node)
        for edge in _get_edges_or_empty(graph, node, get_edges):
            if edge in path or visit(edge):
                return True
        path.remove(node)
        return False

    return any(visit(node) for node in graph)


def topological_sort(graph, get_edges=None):
    """Preform a topological sort on a directed graph, graphs are given in the form {node : [edge1, edge2], ...}

    :param graph: A graph in the form {node : [edge1, edge2], ...}, see get_edges parameter for caveats
    :type graph: dict

    :param get_edges:  If your edge container is not an iterable type, this should be a function
                       that returns an iterable over a series of edges (References to other nodes in the graph)

    :type get_edges: func

    :raises pake.graph.CyclicDependencyException: Raised when a cycle is detected in the given graph.

    :return: A topologically sorted copy of the given graph.
    :rtype: dict
    """

    if get_edges is None:
        def get_edges(t): return t

    graph = dict(graph)
    while graph:
        acyclic = False
        for node, edges in list(graph.items()):
            for edge in get_edges(edges):
                if edge in graph:
                    break
            else:
                acyclic = True
                del graph[node]
                yield (node, edges)
        if not acyclic:
            raise CyclicDependencyException("Cyclic dependency detected.")
