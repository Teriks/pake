
class CyclicDependencyError(Exception):
    pass


def topological_sort(graph_unsorted, get_edges=None):
    if get_edges is None:
        def get_edges(t): return t[1]
    graph_unsorted = dict(graph_unsorted)
    while graph_unsorted:
        acyclic = False
        for node, edges in list(graph_unsorted.items()):
            for edge in get_edges(edges):
                if edge in graph_unsorted:
                    break
            else:
                acyclic = True
                del graph_unsorted[node]
                yield (node, edges)
        if not acyclic:
            raise CyclicDependencyError("Cyclic dependency detected.")
