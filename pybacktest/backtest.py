# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

from pybacktest.blocks import Entry
from pybacktest.blotter import Blotter
from pybacktest.plot import Plotter

__all__ = ['Backtest']


class Performance(object):
    def __init__(self, blotter):
        self.blotter = blotter

    @property
    def equity(self):
        return (self.blotter.continuous_returns + 1).cumprod()

    @property
    def trade_equity(self):
        return (self.blotter.trade_returns + 1).cumprod()

    def __repr__(self):
        return '%s / equity %s / %s trades' % (
            self.__class__.__name__,
            round(self.trade_equity.iloc[-1], 3), self.trade_equity.shape[0])


class BacktestError(Exception):
    pass


class Backtest(object):
    def __init__(self, spec, mark_price=None, txcost_pct=None, txcost_points=None):
        self.spec = spec

        self.txcost_pct = txcost_pct
        self.txcost_points = txcost_points

        if not isinstance(spec, Entry):
            if isinstance(spec, (list, tuple)):
                raise NotImplementedError('Backtest with multiple entries is not supported yet')
            else:
                raise ValueError('Incorrect spec (should be Entry)')

        self.blotter = Blotter(spec, mark_price=mark_price, txcost_percent=txcost_pct, txcost_points=txcost_points)
        self.performance = Performance(self.blotter)
        self.plot = Plotter(self.blotter)

    def __repr__(self):
        return '%s\n%s' % (self.__class__, self.performance)
