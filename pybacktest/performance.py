# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Functions for calculating performance statistics and reporting """

import numpy
import pandas

start = lambda eqd: eqd.index[0]
end = lambda eqd: eqd.index[-1]
days = lambda eqd: (eqd.index[-1] - eqd.index[0]).days
trades_per_month = lambda eqd: eqd.groupby(
    lambda x: (x.year, x.month)
).apply(lambda x: x[x != 0].count()).mean()
profit = lambda eqd: eqd.sum()
average = lambda eqd: eqd[eqd != 0].mean()
average_gain = lambda eqd: eqd[eqd > 0].mean()
average_loss = lambda eqd: eqd[eqd < 0].mean()
winrate = lambda eqd: float(sum(eqd > 0)) / len(eqd)
payoff = lambda eqd: eqd[eqd > 0].mean() / -eqd[eqd < 0].mean()
pf = PF = lambda eqd: abs(eqd[eqd > 0].sum() / eqd[eqd < 0].sum())
maxdd = lambda eqd: (eqd.cumsum() - pandas.expanding_max(eqd.cumsum())).abs().max()
rf = RF = lambda eqd: eqd.sum() / maxdd(eqd)
trades = lambda eqd: len(eqd[eqd != 0])
_days = lambda eqd: eqd.resample('D', how='sum').dropna()


def sharpe(eqd):
    """ daily sharpe ratio """
    d = _days(eqd)
    return (d.mean() / d.std()) ** (252 ** 0.5)


def sortino(eqd):
    """ daily sortino ratio """
    d = _days(eqd)
    return (d.mean() / d[d < 0]).std()


def ulcer(eqd):
    eq = eqd.cumsum()
    return (((eq - pandas.expanding_max(eq)) ** 2).sum() / len(eq)) ** 0.5


def upi(eqd, risk_free=0):
    eq = eqd[eqd != 0]
    return (eq.mean() - risk_free) / ulcer(eq)


UPI = upi


def mpi(eqd):
    """ Modified UPI, with enumerator resampled to months (to be able to
    compare short- to medium-term strategies with different trade frequencies. """
    return eqd.resample('M', how='sum').mean() / ulcer(eqd)


MPI = mpi


def mcmdd(eqd, runs=1000, quantile=0.99, array=False):
    maxdds = [maxdd(eqd.take(numpy.random.permutation(len(eqd)))) for i in range(runs)]
    if not array:
        return pandas.Series(maxdds).quantile(quantile)
    else:
        return maxdds
