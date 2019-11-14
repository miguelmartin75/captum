# TODO: convert to iterable to be a cleaner api
# i.e. to be able to go for stat in stat_graph: ...
class StatGraph(object):
    class Node(object):
        stat = None
        invisible = False

        def __init__(self, stat, invisible):
            self.stat = stat
            self.invisible = invisible

    def __init__(self):
        self.module_to_node = dict()
        self.nodes = []

    # TODO: type annotation
    def add(self, stat):
        if stat in self.module_to_node:
            return self

        node = StatGraph.Node(stat=stat(), invisible=False)
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
        for stat in self.iter_all():
            for name, dep in stat.deps:
                if self.contains(dep):
                    continue
                # TODO: add to beginning of list
                # TODO: handle this better

            continue

    def traverse(self, x=None):
        # TODO
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
        #self._resolve_deps()
        summ = self.traverse()

        return { self.module_to_node[k].stat.name: v for k, v in summ.items() }
        # TODO
        #return { self.module_to_node[k].name: v for k, v in summ.items() if not v.invisible }

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
        self._stat_graph.traverse(x)

    @property
    def summary(self):
        return self._stat_graph.summary

# TODO
def common_aggr(init_fn=None, min_fn=None, max_fn=None):
    return None
    #from captum.aggr.stat import Mean, Var, StdDev, Min, Max
    #return Aggregator([Mean(init_fn=init_fn), Var(init_fn=init_fn), StdDev(), Count(), Min(), Max()])
