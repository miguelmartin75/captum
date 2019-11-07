import numpy as np

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
    def __init__(self, init_fn=np.zeros_like):
        super().__init__()
        self.cumsum = None
        self.init_fn = init_fn
        self.n = 0

    def get(self, deps):
        if self.n == 0:
            return self.cumsum
        return self.cumsum / self.n

    def update(self, x):
        if self.cumsum is None:
            self.cumsum = self.init_fn(x)

        self.cumsum += x
        self.n += 1

    @property
    def name(self):
        return 'mean'

class Var(Stat):
    def __init__(self):
        super().__init__({'mean': Mean})
        self.x_squared = 0
        self.n = 0

    def get(self, deps):
        # TODO
        return self.n

    def update(self, x):
        # TODO
        pass

    @property
    def name(self):
        return 'variance'

class StdDev(Stat):
    def __init__(self):
        super().__init__({'var': Var})

    def get(self, deps):
        return deps['var'] ** 0.5

    def update(self, x):
        pass

    @property
    def name(self):
        return 'std_dev'

# TODO: could use this to implement every fn lmao
class GeneralAccumFn(Stat):
    def __init__(self, fn=None):
        super().__init__()
        self.result = None
        self.fn = fn

    def get(self, deps):
        return self.result

    def update(self, x):
        if self.result is None:
            self.result = x
        else:
            self.result = self.fn(self.result, x)

class Min(GeneralAccumFn):
    def __init__(self, min_fn=np.minimum):
        super().__init__(fn=min_fn)

    @property
    def name(self):
        return 'min'

class Max(GeneralAccumFn):
    def __init__(self, max_fn=np.maximum):
        super().__init__(fn=max_fn)

    @property
    def name(self):
        return 'max'
