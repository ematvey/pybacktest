# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

''' Optimizer class '''

from cached_property import cached_property
import pybacktest
import itertools
import pandas
import numpy


class Optimizer(object):

    def __init__(self, strategy_fn, ohlc, params={}, metrics=['pf', 'sharpe', 'maxdd', 'mpi', 'average', 'trades']):
        self.strategy_fn = strategy_fn
        self.ohlc = ohlc
        self.metrics = metrics
        assert all([len(p) == 3 for p in params.values()]), 'Wrong params specified'
        self.params = params.copy()

    def add_param(self, param, start, stop, step):
        self.params[param] = [start, stop, step]

    @cached_property(ttl=0)
    def results(self):
        print '[ running optimization, please wait ]'
        p = self.params
        pn = p.keys()
        results = []
        cartesian = [numpy.arange(p[k][0], p[k][1]+.000001, p[k][2]) for k in pn]
        for pvals in itertools.product(*cartesian):
            pset = dict(zip(pn, pvals))
            bt = pybacktest.Backtest(self.strategy_fn(self.ohlc, **pset))
            r = {}
            for m in self.metrics:
                r[m] = getattr(bt.stats, m)
            r.update(pset)
            results.append(r)
        return pandas.DataFrame(results)

    def best_by(self, name, depth=20):
        res = self.results
        return res[res[name].notnull()].sort(name, ascending=False).head(depth)
