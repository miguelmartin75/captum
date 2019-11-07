# TODO: convert to iterable to be a cleaner api
# i.e. to be able to go for stat in stat_graph: ...
class StatGraph(object):
    def __init__(self):
        self.is_ready = False
        self.module_to_node = dict()
        self.nodes = []

    # TODO: type annotation
    def add(self, stat):
        if stat.__class__ in self.module_to_node:
            return self

        self.is_ready = False
        self.module_to_node[stat.__class__] = stat
        self.nodes.append(stat)
        return self

    def construct(self):
        self._resolve_deps()
        # TODO: 
        # we're currently assuming this is already topologically sorted, which is a fair assumption
        #self.nodes = list(self._topo_sort())
        self.is_ready = True

    def _resolve_deps(self):
        pass
#        for node in self.nodes:
#            self.deps[node] = {}
#            for name, dep in node.stat.deps.items():
#                assert dep in self.module_to_node
#                self.deps[node][name] = self.module_to_node[dep.__class__]

    def iter_all(self):
        if not self.is_ready:
            self.construct()

        for stat in self.nodes:
            yield stat

    @property
    def summary(self):
        summ = {}
        for stat in self.iter_all():
            deps = {}

            for name, module in stat.deps.items():
                assert module in summ
                deps[name] = summ[module]

            summ[stat.__class__] = stat.get(deps)

        return { self.module_to_node[k].name: v for k, v in summ.items() }

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
        for stat in self._stat_graph.iter_all():
            stat.update(x)

    @property
    def summary(self):
        return self._stat_graph.summary

# TODO
def common_aggr(init_fn=None, min_fn=None, max_fn=None):
    return None
    #from captum.aggr.stat import Mean, Var, StdDev, Min, Max
    #return Aggregator([Mean(init_fn=init_fn), Var(init_fn=init_fn), StdDev(), Count(), Min(), Max()])
