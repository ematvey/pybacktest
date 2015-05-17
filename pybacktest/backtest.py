# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

from __future__ import print_function
import time

from pandas.lib import cache_readonly

import pandas
from . import parts, performance


__all__ = ['Backtest']


class StatEngine(object):
    def __init__(self, equity_fn):
        self._stats = [i for i in dir(performance) if not i.startswith('_')]
        self._equity_fn = equity_fn

    def __dir__(self):
        return dir(type(self)) + self._stats

    def __getattr__(self, attr):
        if attr in self._stats:
            equity = self._equity_fn()
            fn = getattr(performance, attr)
            try:
                return fn(equity)
            except:
                return
        else:
            raise IndexError(
                "Calculation of '%s' statistic is not supported" % attr)


class ContextWrapper(object):
    def __init__(self, *args, **kwargs):
        pass


class Backtest(object):
    """
    Backtest (Pandas implementation of vectorized backtesting).

    Lazily attempts to extract multiple pandas.Series with signals and prices
    from a given namespace and combine them into equity curve.

    Attempts to be as smart as possible.

    """

    _ohlc_possible_fields = ('ohlc', 'bars', 'ohlcv')
    _sig_mask_int = ('Buy', 'Sell', 'Short', 'Cover')
    _pr_mask_int = ('BuyPrice', 'SellPrice', 'ShortPrice', 'CoverPrice')

    def __init__(self, dataobj, name='Unknown',
                 signal_fields=('buy', 'sell', 'short', 'cover'),
                 price_fields=('buyprice', 'sellprice', 'shortprice',
                               'coverprice')):
        """
        Arguments:

        *dataobj* should be dict-like structure containing signal series.
        Easiest way to define is to create pandas.Series with exit and entry
        signals and pass whole local namespace (`locals()`) as dataobj.

        *name* is simply backtest/strategy name. Will be user for printing,
        potting, etc.

        *signal_fields* specifies names of signal Series that backtester will
        attempt to extract from dataobj. By default follows AmiBroker's naming
        convention.

        *price_fields* specifies names of price Series where trades will take
        place. If some price is not specified (NaN at signal's timestamp, or
        corresponding Series not present in dataobj altogather), defaults to
        Open price of next bar. By default follows AmiBroker's naming
        convention.

        Also, dataobj should contain dataframe with Bars of underlying
        instrument. We will attempt to guess its name before failing miserably.

        To get a hang of it, check out the examples.

        """
        self._dataobj = dict([(k.lower(), v) for k, v in dataobj.iteritems()])
        self._sig_mask_ext = signal_fields
        self._pr_mask_ext = price_fields
        self.name = name
        self.trdplot = self.sigplot = parts.Slicer(self.plot_trades,
                                                   obj=self.ohlc)
        self.eqplot = parts.Slicer(self.plot_equity, obj=self.ohlc)
        self.run_time = time.strftime('%Y-%d-%m %H:%M %Z', time.localtime())
        self.stats = StatEngine(lambda: self.equity)

    def __repr__(self):
        return "Backtest(%s, %s)" % (self.name, self.run_time)

    @property
    def dataobj(self):
        return self._dataobj

    @cache_readonly
    def signals(self):
        return parts.extract_frame(self.dataobj, self._sig_mask_ext,
                                   self._sig_mask_int).fillna(value=False)

    @cache_readonly
    def prices(self):
        return parts.extract_frame(self.dataobj, self._pr_mask_ext,
                                   self._pr_mask_int)

    @cache_readonly
    def default_price(self):
        return self.ohlc.O  # .shift(-1)

    @cache_readonly
    def trade_price(self):
        pr = self.prices
        if pr is None:
            return self.ohlc.O  # .shift(-1)
        dp = pandas.Series(dtype=float, index=pr.index)
        for pf, sf in zip(self._pr_mask_int, self._sig_mask_int):
            s = self.signals[sf]
            p = self.prices[pf]
            dp[s] = p[s]
        return dp.combine_first(self.default_price)

    @cache_readonly
    def positions(self):
        return parts.signals_to_positions(self.signals,
                                          mask=self._sig_mask_int)

    @cache_readonly
    def trades(self):
        p = self.positions.reindex(
            self.signals.index).ffill().shift().fillna(value=0)
        p = p[p != p.shift()]
        tp = self.trade_price
        assert p.index.tz == tp.index.tz, "Cant operate on singals and prices " \
                                          "indexed as of different timezones"
        t = pandas.DataFrame({'pos': p})
        t['price'] = tp
        t = t.dropna()
        t['vol'] = t.pos.diff()
        return t.dropna()

    @cache_readonly
    def equity(self):
        return parts.trades_to_equity(self.trades)

    @cache_readonly
    def ohlc(self):
        for possible_name in self._ohlc_possible_fields:
            s = self.dataobj.get(possible_name)
            if not s is None:
                return s
        raise Exception("Bars dataframe was not found in dataobj")

    @cache_readonly
    def report(self):
        return performance.performance_summary(self.equity)

    def summary(self):
        import yaml

        s = '|  %s  |' % self
        print('-' * len(s))
        print(s)
        print('-' * len(s), '\n')
        print(yaml.dump(self.report, allow_unicode=True, default_flow_style=False))
        print('-' * len(s))

    def plot_equity(self, subset=None):
        if subset is None:
            subset = slice(None, None)
        assert isinstance(subset, slice)
        eq = self.equity[subset].cumsum()
        eq.plot(color='red', label='strategy')
        ix = self.ohlc.ix[eq.index[0]:eq.index[-1]].index
        price = self.ohlc.C
        (price[ix] - price[ix][0]).resample('W', how='first').dropna() \
            .plot(color='black', alpha=0.5, label='underlying')

        import matplotlib.pylab as pylab

        pylab.legend(loc='best')
        pylab.title('%s\nEquity' % self)

    def plot_trades(self, subset=None):
        if subset is None:
            subset = slice(None, None)
        fr = self.trades.ix[subset]
        le = fr.price[(fr.pos > 0) & (fr.vol > 0)]
        se = fr.price[(fr.pos < 0) & (fr.vol < 0)]
        lx = fr.price[(fr.pos.shift() > 0) & (fr.vol < 0)]
        sx = fr.price[(fr.pos.shift() < 0) & (fr.vol > 0)]

        import matplotlib.pylab as pylab

        pylab.plot(le.index, le.values, '^', color='lime', markersize=12,
                   label='long enter')
        pylab.plot(se.index, se.values, 'v', color='red', markersize=12,
                   label='short enter')
        pylab.plot(lx.index, lx.values, 'o', color='lime', markersize=7,
                   label='long exit')
        pylab.plot(sx.index, sx.values, 'o', color='red', markersize=7,
                   label='short exit')
        eq = self.equity.ix[subset].cumsum()
        ix = eq.index
        (eq + self.ohlc.O[ix[0]]).plot(color='red', style='-')
        # self.ohlc.O.ix[ix[0]:ix[-1]].plot(color='black', label='price')
        self.ohlc.O.ix[subset].plot(color='black', label='price')
        pylab.title('%s\nTrades for %s' % (self, subset))
