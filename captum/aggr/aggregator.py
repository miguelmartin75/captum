# TODO: convert to iterable to be a cleaner api
# i.e. to be able to go for stat in stat_graph: ...
class StatGraph(object):
    class Node:
        stat = None
        invisible = False

        def __init__(self, stat, invisible=False):
            self.stat = stat
            self.invisible = invisible

    # stats is a dict
    def __init__(self):
        self.is_ready = False
        self.nodes = []

        # module -> node
        self.module_to_node = dict()

        # class name -> deps
        self.deps = dict()

    # TODO: type annotation
    def add(self, stat, invisible=False):
        if stat in self.module_to_node:
            self.module_to_node[stat].invisible = invisible
            return self

        self.is_ready = False
        node = StatGraph.Node(stat=stat(), invisible=invisible)
        self.module_to_node[stat] = node
        self.nodes.append(node)
        return self

    def construct(self):
        self._resolve_deps()
        # TODO: 
        # we're currently assuming this is already topologically sorted, which is a fair assumption
        #self.nodes = list(self._topo_sort())
        self.is_ready = True

    def _resolve_deps(self):
        for node in self.nodes:
            self.deps[node] = {}
            for name, dep in node.stat.deps.items():
                if dep not in self.module_to_node:
                    self.add(dep, invisible=True)

                self.deps[node][name] = self.module_to_node[dep]

    def iter_all(self):
        if not self.is_ready:
            self.construct()

        for stat in self.nodes:
            yield stat

    @property
    def summary(self):
        summ = {}
        for node in self.iter_all():
            if node.invisible:
                continue

            summ[node.stat.name] = node.stat.get(self.deps[node])
        return summ

# TODO: 
# should we let update accept a dict to be more generic?
# or just let the user handle that on the user-side?
class Aggregator(object):
    def __init__(self, stats=None):
        self._stat_graph = StatGraph()
        self.add_all(stats)

    def add_all(self, stats):
        for stat in stats:
            self.add(stat)
        return self

    def add(self, stat):
        self._stat_graph.add(stat)
        return self

    def update(self, x):
        for node in self._stat_graph.iter_all():
            node.stat.update(x)

    @property
    def summary(self):
        return self._stat_graph.summary

# TODO: 
# work out how to supply stats with a custom n? 
#
# e.g. 
# if a stat is aggregating over some f(batch)... how does this work?
