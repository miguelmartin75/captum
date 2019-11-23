#!/usr/bin/env python3
import torch

from captum.attr._core.aggregator import common_aggr
from .helpers.utils import BaseTest


class Test(BaseTest):
    def test_single_input(self):
        size = (2, 3)
        aggr = common_aggr()
        for _ in range(10):
            attrs = torch.randn(size)
            aggr.update(attrs)

        summ = aggr.summary
        self.assertIsNotNone(summ)
        self.assertTrue(isinstance(summ, dict))

        for k in summ:
            self.assertTrue(summ[k].size() == size)

    def test_multi_input(self):
        size1 = (10, 5, 5)
        size2 = (3, 5)

        aggr = common_aggr()
        for _ in range(10):
            a1 = torch.randn(size1)
            a2 = torch.randn(size2)
            aggr.update((a1, a2))

        summ = aggr.summary
        self.assertIsNotNone(summ)
        self.assertTrue(len(summ) == 2)
        self.assertTrue(isinstance(summ[0], dict))
        self.assertTrue(isinstance(summ[1], dict))

        for k in summ[0]:
            self.assertTrue(summ[0][k].size() == size1)
            self.assertTrue(summ[1][k].size() == size2)
