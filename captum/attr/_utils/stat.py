#!/usr/bin/env python3
import torch
from torch import Tensor
from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from captum.attr._utils.summarizer import SummarizerSingleTensor


class Stat:
    """
    The Stat class represents a statistic that can be updated and retrieved
    at any point in time.

    The basic functionality this class provides is:
    1. A update/get method to actually compute the statistic
    2. A statistic store/cache to retrieve dependent information
       (e.g. other stat values that are required for computation)
    3. The name of the statistic that is used for the user to refer to
    """

    def __init__(self, name: Optional[str] = None, **kwargs: Any):
        self.params = kwargs
        self._name = name

        self._other_stats: Optional[SummarizerSingleTensor] = None

    def init(self):
        pass

    def _get_stat(self, stat: 'Stat') -> Optional['Stat']:
        assert self._other_stats is not None
        return self._other_stats.get(stat)

    def update(self, x: Tensor):
        raise NotImplementedError()

    def get(self) -> Optional[Tensor]:
        raise NotImplementedError()

    def __hash__(self):
        return hash((self.__class__, frozenset(self.params.items())))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Stat):
            return self.__class__ == other.__class__ and frozenset(
                self.params.items()
            ) == frozenset(other.params.items())
        else:
            return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    @property
    def name(self):
        """
        The name of the statistic. i.e. it is the key in a .summary

        See Summarizer or SummarizerSingleTensor
        """
        default_name = self.__class__.__name__.lower()
        if len(self.params) > 0:
            default_name += f"({self.params})"

        return default_name if self._name is None else self._name


class Count(Stat):
    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name)
        self.n = None

    def get(self):
        return self.n

    def update(self, x):
        if self.n is None:
            self.n = 0
        self.n += 1


class Mean(Stat):
    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name)
        self.rolling_mean: Optional[Tensor] = None
        self.n: Optional[Count] = None

    def get(self) -> Optional[Tensor]:
        return self.rolling_mean

    def init(self):
        self.n = self._get_stat(Count())

    def update(self, x):
        n = self.n.get()

        if self.rolling_mean is None:
            self.rolling_mean = x
        else:
            delta = x - self.rolling_mean
            self.rolling_mean += delta / n


class MSE(Stat):
    def __init__(self, name: Optional[str] = None):
        super().__init__(name=name)
        self.prev_mean = None
        self.mse = None

    def init(self):
        self.mean = self._get_stat(Mean())

    def get(self) -> Optional[Tensor]:
        if self.mse is None and self.prev_mean is not None:
            return torch.zeros_like(self.prev_mean)
        return self.mse

    def update(self, x: Tensor):
        mean = self.mean.get()

        if mean is not None and self.prev_mean is not None:
            rhs = (x - self.prev_mean) * (x - mean)
            if self.mse is None:
                self.mse = rhs
            else:
                self.mse += rhs

        # do not not clone
        self.prev_mean = mean.clone()


class Var(Stat):
    def __init__(self, name: Optional[str] = None, order: int = 0):
        if name is None:
            if order == 0:
                name = "variance"
            elif order == 1:
                name = "sample_variance"
            else:
                name = f"variance({order})"

        super().__init__(name=name, order=order)
        self.order = order

    def init(self):
        self.mse = self._get_stat(MSE())
        self.n = self._get_stat(Count())

    def update(self, x: Tensor):
        pass

    def get(self) -> Optional[Tensor]:
        mse = self.mse.get()
        n = self.n.get()

        if mse is None:
            return None

        if n <= self.order:
            return torch.zeros_like(mse)

        return mse / (n - self.order)


class StdDev(Stat):
    def __init__(self, name: Optional[str] = None, order: int = 0):
        if name is None:
            if order == 0:
                name = "std_dev"
            elif order == 1:
                name = "sample_std_dev"
            else:
                name = f"std_dev{order})"

        super().__init__(name=name, order=order)
        self.order = order

    def init(self):
        self.var = self._get_stat(Var(order=self.order))

    def update(self, x: Tensor):
        pass

    def get(self) -> Optional[Tensor]:
        var = self.var.get()
        return var ** 0.5 if var is not None else None


class GeneralAccumFn(Stat):
    def __init__(self, fn: Callable, name: Optional[str] = None):
        super().__init__(name=name)
        self.result = None
        self.fn = fn

    def get(self) -> Optional[Tensor]:
        return self.result

    def update(self, x):
        if self.result is None:
            self.result = x
        else:
            self.result = self.fn(self.result, x)


class Min(GeneralAccumFn):
    def __init__(self, name: Optional[str] = None, min_fn: Callable = torch.min):
        super().__init__(name=name, fn=min_fn)


class Max(GeneralAccumFn):
    def __init__(self, name: Optional[str] = None, max_fn: Callable = torch.max):
        super().__init__(name=name, fn=max_fn)


class Sum(GeneralAccumFn):
    def __init__(self, name: Optional[str] = None, add_fn: Callable = torch.add):
        super().__init__(name=name, fn=add_fn)

def CommonStats() -> List[Stat]:
    r"""
    Returns common summary statistics, specifically:
        Mean, Sample Variance, Sample Std Dev, Min, Max
    """
    return [Mean(), Var(order=1), StdDev(order=1), Min(), Max()]
