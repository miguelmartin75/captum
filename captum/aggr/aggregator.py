class StatGraph(object):
    class Node(object):
        stat = None
        invisible = False

        def __init__(self, stat, invisible):
            self.stat = stat
            self.invisible = invisible

    def __init__(self):
        self.is_ready = False
        self.module_to_node = dict()
        self.nodes = []

    def add(self, stat, invisible=False):
        if stat in self.module_to_node:
            return self

        self.is_ready = False
        node = StatGraph.Node(stat=stat(), invisible=invisible)
        self.nodes.append(node)
        self.module_to_node[stat] = node
        return self

    def iter_all(self, visible=True):
        for node in self.nodes:
            if visible and node.invisible:
                continue

            yield node.stat

    def contains(self, stat_module):
        return stat_module in self.module_to_node

    def _resolve_deps(self):
        unsat = False
        for stat in self.iter_all(visible=False):
            for name, dep in stat.deps.items():
                if not self.contains(dep):
                    self.add(dep, invisible=True)
                    unsat = True
        
        if unsat:
            self._resolve_deps()
        else:
            self.nodes = list(self._topo_order())
            self.is_ready = True

    # TODO: add tests
    def _dfs(self, node, visited):
        for name, module in node.stat.deps.items():
            parent = self.module_to_node[module]
            if parent in visited:
                continue

            for x in self._dfs(parent, visited):
                yield x
        
        visited.add(node)
        yield node

    # TODO: add tests
    def _topo_order(self):
        visited = set()
        order = []
        for node in self.nodes:
            if node in visited:
                continue

            for node in self._dfs(node, visited):
                order.append(node)

        return order

    def traverse(self, x=None):
        if not self.is_ready:
            self._resolve_deps()

        summ = {}
        for stat in self.iter_all(visible=False):
            deps = {}

            for name, module in stat.deps.items():
                assert module in summ
                deps[name] = summ[module]

            if x is not None:
                stat.update(x, deps)

            summ[stat.__class__] = stat.get(deps)

        return summ

    @property
    def summary(self):
        summ = self.traverse()

        return { self.module_to_node[k].stat.name: v for k, v in summ.items() \
                 if not self.module_to_node[k].invisible }

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
        self._stat_graph.traverse(x)

    @property
    def summary(self):
        return self._stat_graph.summary

def common_aggr():
    from captum.aggr.stat import Mean, Var, StdDev, SampleStdDev, Min, Max
    return Aggregator([Mean, Var, StdDev, SampleStdDev, Min, Max])
