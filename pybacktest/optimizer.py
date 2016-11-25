# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Optimizer class """

from cached_property import cached_property
from pybacktest.backtest import Backtest

import itertools
import pandas
import numpy
import multiprocessing


def _embedded_backtest(args_tuple):
    params, strategy_fn, ohlc, metrics = args_tuple
    bt = Backtest(strategy_fn(ohlc, **params))
    r = {}
    for m in metrics:
        r[m] = getattr(bt.stats, m)
    r.update(params)
    return r


class Optimizer(object):

    def __init__(self, strategy_fn, ohlc, params={},
                 metrics=['pf', 'sharpe', 'maxdd', 'mpi', 'average', 'trades'],
                 processes=None):
        ''' `strategy_fn` - Backtest-compatible strategy function.

        `ohlc` - Backtest- and strategy-compatible dataframe.

        `metrics` - Backtest-compatible set of metrics.

        `processes` - pass 1 to use single (this) process, pass None to use
        #processes = #cores, or specify exact number of processes to use.

        '''
        self.strategy_fn = strategy_fn
        self.ohlc = ohlc
        self.metrics = metrics
        assert all([len(p) == 3 for p in list(params.values())]), 'Wrong params specified'
        self.params = params.copy()
        self.processes = processes

    def add_param(self, param, start, stop, step):
        self.params[param] = [start, stop, step]

    @cached_property
    def results(self):
        p = self.params
        pn = list(p.keys())
        results = []
        param_space = [
            dict(list(zip(pn, pset))) for pset in
            itertools.product(
                *[numpy.arange(p[k][0], p[k][1]+.000001, p[k][2]) for k in pn]
            )
        ]

        args_gen = zip(param_space,
                                  itertools.repeat(self.strategy_fn),
                                  itertools.repeat(self.ohlc),
                                  itertools.repeat(self.metrics))

        if self.processes != 1:
            pool = multiprocessing.Pool(self.processes)
            try:
                results = pool.map(_embedded_backtest, args_gen)
            except KeyboardInterrupt:
                pool.close()
                pool.join()
        else:
            results = []
            for a in args_gen:
                results.append(_embedded_backtest(a))

        return pandas.DataFrame(results)

    def best_by(self, name, depth=20):
        res = self.results
        return res[res[name].notnull()].sort(name, ascending=False).head(depth)
