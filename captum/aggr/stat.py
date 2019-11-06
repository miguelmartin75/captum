from types import ModuleType

class Stat(object):
    def __init__(self, deps=None):
        if deps is None:
            deps = {}
        self.deps = deps

    def get(self, deps):
        raise NotImplementedError()

    def update(self, x):
        raise NotImplementedError()

    @property
    def name(self):
        return 'stat'

class Mean(Stat):
    def __init__(self):
        super().__init__()
        self.cumsum = None
        self.n = 0

    def get(self, deps):
        if self.n == 0:
            return self.cumsum
        return self.cumsum / self.n

    def update(self, x):
        if not self.cumsum:
            self.cumsum = torch.zeros_like(x)

        self.cumsum += x
        self.n += 1

    @property
    def name(self):
        return 'mean'

class Var(Stat):
    def __init__(self):
        super().__init__({'mean': Mean})

    def get(self, deps):
        # TODO
        raise NotImplementedError()

    def update(self, x):
        # TODO
        raise NotImplementedError()

    @property
    def name(self):
        return 'variance'

class StdDev(Stat):
    def __init__(self):
        super().__init__({'var': Var})

    def get(self, deps):
        return deps['var'].get() ** 0.5

    def update(self, x):
        pass

    @property
    def name(self):
        return 'std_dev'
