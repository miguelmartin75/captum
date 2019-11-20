import torch

class Stat(object):
    def __init__(self, deps=None):
        if deps is None:
            deps = {}
        self.deps = deps

    def get(self, deps):
        raise NotImplementedError()

    def update(self, x, deps):
        raise NotImplementedError()

    @property
    def name(self):
        return 'stat'

class Count(Stat):
    def __init__(self):
        super().__init__()
        self.n = None
    
    def get(self, deps):
        return self.n

    def update(self, x, deps):
        # TODO: figure out how 
        #       to handle sparse input(s)
        if self.n is None:
            self.n = 0
        self.n += 1

    @property
    def name(self):
        return 'count'

class Mean(Stat):
    def __init__(self):
        super().__init__({'n': Count})
        self.cumsum = None

    def get(self, deps):
        n = deps['n']
        if n == 0:
            return self.cumsum
        return self.cumsum / n

    def update(self, x, deps):
        if self.cumsum is None:
            self.cumsum = torch.zeros_like(x)

        self.cumsum += x

    @property
    def name(self):
        return 'mean'

class MSE(Stat):
    def __init__(self):
        super().__init__({'mean': Mean})
        self.prev_mean = None
        self.mse = None

    def get(self, deps):
        return self.mse

    def update(self, x, deps):
        mean = deps['mean']
        if mean is None or \
           self.prev_mean is None:
            self.prev_mean = mean
            return None

        rhs = (x - self.prev_mean) * (x - mean)
        if self.mse is None:
            self.mse = rhs
        else:
            self.mse += rhs

        self.prev_mean = mean

    @property
    def name(self):
        return 'mse'

class Var(Stat):
    def __init__(self):
        super().__init__({'mse': MSE, 'count': Count})

    def get(self, deps):
        mse = deps['mse']
        n = deps['count']
        return mse / n if mse is not None else None

    def update(self, x, deps):
        pass

    @property
    def name(self):
        return 'variance'

class StdDev(Stat):
    def __init__(self):
        super().__init__({'var': Var})

    def get(self, deps):
        var = deps['var']
        return var ** 0.5 if var is not None else None

    def update(self, x, deps):
        pass

    @property
    def name(self):
        return 'std_dev'

class SampleVar(Stat):
    def __init__(self):
        super().__init__({'mse': MSE, 'count': Count})

    def get(self, deps):
        mse = deps['mse']
        n = deps['count']
        if n - 1 <= 0 or mse is None:
            return None

        return mse / (n - 1)

    def update(self, x, deps):
        pass

    @property
    def name(self):
        return 'sample_variance'

class SampleStdDev(Stat):
    def __init__(self):
        super().__init__({'var': SampleVar})

    def get(self, deps):
        # TODO: be DRY
        var = deps['var']
        return var ** 0.5 if var is not None else None

    def update(self, x, deps):
        pass

    @property
    def name(self):
        return 'sample_std_dev'

class GeneralAccumFn(Stat):
    def __init__(self, fn):
        super().__init__()
        self.result = None
        self.fn = fn

    def get(self, deps):
        return self.result

    def update(self, x, deps):
        if self.result is None:
            self.result = x
        else:
            self.result = self.fn(self.result, x)

class Min(GeneralAccumFn):
    def __init__(self, min_fn=torch.min):
        super().__init__(fn=min_fn)

    @property
    def name(self):
        return 'min'

class Max(GeneralAccumFn):
    def __init__(self, max_fn=torch.max):
        super().__init__(fn=max_fn)

    @property
    def name(self):
        return 'max'
