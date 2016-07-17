# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Functions for calculating performance statistics and reporting """

import pandas
import numpy



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
    ''' daily sharpe ratio '''
    d = _days(eqd)
    return (d.mean() / d.std()) * (252**0.5)


def sortino(eqd):
    ''' daily sortino ratio '''
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
    maxdds = [maxdd(eqd.take(numpy.random.permutation(len(eqd)))) for i in xrange(runs)]
    if not array:
        return pandas.Series(maxdds).quantile(quantile)
    else:
        return maxdds


def holding_periods(eqd):
    # rather crude, but will do
    return pandas.Series(eqd.index.to_datetime(), index=eqd.index, dtype=object).diff().dropna()


def performance_summary(equity_diffs, quantile=0.99, precision=4):
    def force_quantile(series, q):
        return sorted(series.values)[int(len(series) * q)]
    eqd = equity_diffs[equity_diffs != 0]
    if getattr(eqd.index, 'tz', None) is not None:
        eqd = eqd.tz_convert(None)
    if len(eqd) == 0:
        return {}
    hold = holding_periods(equity_diffs)
    return {
        'backtest': {
            'from': str(eqd.index[0]),
            'to': str(eqd.index[-1]),
            'days': (eqd.index[-1] - eqd.index[0]).days,
            'trades': len(eqd),
            },
        'exposure': {
            'trades/month': round(eqd.groupby(
                    lambda x: (x.year, x.month)
                    ).apply(lambda x: x[x != 0].count()).mean(), precision),
            #'holding periods': {
            #    'max': str(hold.max()),
            #    'median': str(force_quantile(hold, 0.5)),
            #    'min': str(hold.min()),
            #    }
            },
        'performance': {
            'profit': round(eqd.sum(), precision),
            'averages': {
                'trade': round(eqd.mean(), precision),
                'gain': round(eqd[eqd > 0].mean(), precision),
                'loss': round(eqd[eqd < 0].mean(), precision),
                },
            'winrate': round(float(sum(eqd > 0)) / len(eqd), precision),
            'payoff': round(eqd[eqd > 0].mean() / -eqd[eqd < 0].mean(), precision),
            'PF': round(abs(eqd[eqd > 0].sum() / eqd[eqd < 0].sum()), precision),
            'RF': round(eqd.sum() / maxdd(eqd), precision),
            },
        'risk/return profile': {
            'sharpe': round(eqd.mean() / eqd.std(), precision),
            'sortino': round(eqd.mean() / eqd[eqd < 0].std(), precision),
            'maxdd': round(maxdd(eqd), precision),
            'WCDD (monte-carlo %s quantile)' % quantile: round(mcmdd(eqd, quantile=quantile), precision),
            'UPI': round(UPI(eqd), precision),
            'MPI': round(MPI(eqd), precision),
            }
        }
