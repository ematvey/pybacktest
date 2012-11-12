import matplotlib.pyplot
import numpy
import pandas
import datetime
import logging

import performance_statistics


class TradeError(Exception):
    pass


class EquityCalculator(object):
    ''' Calculates EquityCurve from trades and price changes.
        The idea is to keep track of equity changes on trade and on every price
        change separately. '''

    def __init__(self, full_curve=None, trades_curve=None, log_level=None):
        self._full_curve = full_curve or EquityCurve(log_level=log_level)
        self._trades_curve = trades_curve or EquityCurve(log_level=log_level)
        self._full_curve_merged = EquityCurve(log_level=log_level)
        self._trades_curve_merged = EquityCurve(log_level=log_level)
        self.pos = 0
        self.var = 0
        self.now = None
        self.price = None
        self.log = logging.getLogger(self.__class__.__name__)
        if log_level:
            self.log.setLevel(log_level)
        self.log_level = log_level

    def new_price(self, timestamp, price):
        ''' Account for a new price.
            Call this every time an information about tested asset's
            price changes. '''
        self.now = timestamp
        self.price = price
        self._full_curve.add_point(timestamp, self.var + self.pos * price)

    def new_trade(self, timestamp, price, volume):
        ''' Account for a new trade.
            Call this every time strategy makes a trade. '''
        self.var -= price * volume
        self.pos += volume
        equity = self.var + self.pos * price
        diff = equity - sum(self._trades_curve._changes)
        if diff != 0:
            self.log.debug('new equity point %s registered on %s', equity,
                           timestamp)
            self.log.debug('equity change: %s', diff)
        self._trades_curve.add_point(timestamp, equity)
        self._trades_curve.add_trade(timestamp, price, volume)

    def merge(self, record_trades=True):
        ''' Record current results and prepare to start calculating equity
            from the scratch. Purpose: to be able to backtest single strategy
            on a whole basket of instruments. '''
        if self.pos != 0:
            raise Exception('Merge requested when position != 0')
        self._full_curve_merged.merge(self._full_curve,
                keep_trades=(len(self._full_curve_merged) == 0 or
                             len(self._full_curve) == 0))
        self._full_curve = EquityCurve(log_level=self.log_level)
        self._trades_curve_merged.merge(self._trades_curve,
                keep_trades=(len(self._trades_curve_merged) == 0 or
                             len(self._trades_curve) == 0))
        self._trades_curve = EquityCurve(log_level=self.log_level)
        self.var = 0

    @property
    def full_curve(self):
        ''' Return full equity curve (i.e. curve that tracked equity changes on
            every price change, even between the trades). '''
        if not len(self._full_curve) == 0:
            self.merge()
        return self._full_curve_merged

    @property
    def trades_curve(self):
        ''' Return trades equity curve (i.e. curve that tracked equity changes
            only on trades. '''
        if not len(self._trades_curve) == 0:
            self.merge()
        return self._trades_curve_merged


class EquityCurve(object):
    ''' Keeps history of equity changes and calculates various performance
        statistics. Optional: keeps track of trades. '''

    plt = matplotlib.pyplot

    def __init__(self, log_level=None):
        self._changes = list()
        self._times = list()
        self._cumsum = 0
        self.trades = dict()
        self.log = logging.getLogger(self.__class__.__name__)
        if log_level:
            self.log.setLevel(log_level)
        self.log_level = log_level

    def __len__(self):
        return len(self._changes)

    def add_change(self, timestamp, equity_change):
        self._changes.append(equity_change)
        self._cumsum += equity_change
        self._times.append(timestamp)

    def add_point(self, timestamp, equity):
        self._changes.append(equity - self._cumsum)
        self._cumsum = equity
        self._times.append(timestamp)

    def add_trade(self, timestamp, price, volume):
        ''' Add trade. Not used in any computation currently. '''
        if volume != 0:
            if timestamp in self.trades:
                self.log.debug("trade with timestamp %s is already present,"
                               " incrementing timestamp by 1 mcs" %
                               timestamp)
                self.add_trade(timestamp + datetime.timedelta(0, 0, 1),
                               price, volume)
            else:
                self.trades[timestamp] = (price, volume)
        else:
            self.log.warning("trade with 0 volume: %s %s %s", timestamp,
                             price, volume)

    def series(self, mode='equity', frequency=None):
        ''' Pandas TimeSeries object of equity/changes.
        * `mode` determines type, could be "equity" for cumulative equity
           dynamic or "changes" for time series of changes between neighbour
           equity points.
        * `frequency` is pandas-compatible object for frequency conversions.
           (e.g. "D" for daily, "M" for monthly, "5min" for obvious.) '''
        if not frequency:
            if mode == 'equity':
                return pandas.TimeSeries(data=numpy.cumsum(self._changes),
                                         index=self._times)
            elif mode == 'changes':
                return pandas.TimeSeries(data=self._changes, index=self._times)
        else:
            ts = pandas.TimeSeries(data=numpy.cumsum(self._changes),
                                   index=self._times).asfreq(frequency,
                                                             method='ffill')
            ts = ts - ts.shift(1)
            ts = ts[ts != 0]
            if mode == 'changes':
                return ts
            elif mode == 'equity':
                return ts.cumsum()
        raise Exception('Unsupported requirements (probably)')

    def __getitem__(self, stat, precision=2):
        ''' Calculate statistic `stat` on equity dynamics '''
        if len(self._changes) == 0:
            raise Exception('Cannot calculate statistics on empty EquityCurve')
        s = stat.lower()
        func = getattr(performance_statistics, stat.lower(), None)
        if func:
            stat = func(numpy.array(self._changes))
            if isinstance(stat, float):
                stat = round(stat, precision)
            return stat
        else:
            raise KeyError('Cannot calculate statistic with name `%s`', stat)

    def statistics(self, mode='fast'):
        ''' Calculate all possible statistics, as specified in
            `performance_statistics` '''
        if mode == 'full':
            return dict((k, self[k]) for k in performance_statistics.full)
        if mode == 'fast':
            return dict((k, self[k]) for k in performance_statistics.fast)
        else:
            raise Exception('Unsupported `mode` of statistics request')

    def merge(self, curve, overwrite=True, keep_trades=False):
        ''' Merge two curves by differentials.
            Will overwrite self unless `overwrite` was set to False.
            Set `keep_trades` to True if you want to try to keep recorded trades
            (could be problematic since they are supposedly two different
            instruments.'''
        changes1 = self._changes
        changes2 = curve._changes
        times1 = self._times
        times2 = curve._times
        if len(changes1) == 0:
            if overwrite:
                self._changes = curve._changes
                self._times = curve._times
                self.trades = curve.trades
                return
            else:
                return curve
        if len(changes2) == 0:
            return self * overwrite or None
        i = j = 0
        changes = []
        times = []
        while i < len(changes1) or j < len(changes2):
            if i < len(changes1) and j < len(changes2) and \
                    times1[i] == times2[j]:
                times.append(times1[i])
                changes.append(changes1[i] + changes2[j])
                i += 1
                j += 1
            elif j >= len(changes2) or i < len(changes1) and \
                    times1[i] < times2[j]:
                times.append(times1[i])
                changes.append(changes1[i])
                i += 1
            elif i >= len(changes1) or j < len(changes2) and \
                    times1[i] > times2[j]:
                times.append(times2[j])
                changes.append(changes2[j])
                j += 1
            else:
                raise Exception("EquityCurve merge error")
        if keep_trades:
            trades = self.trades.copy()
            if hasattr(self, 'trades'):
                if len(curve.trades) != 0:
                    if len(trades) == 0:
                        trades = curve.trades
                    elif len(curve.trades) != 0:
                        for time in curve.trades.keys():
                            if time in self.trades:
                                raise Exception("EquityCurve merge error: "
                                                "attempting to merge a trade "
                                                "with non-unique timestamp")
                        self.trades.update(curve.trades)
        if overwrite:
            self._changes = changes
            self._times = times
            if keep_trades:
                self.trades = trades
            else:
                if hasattr(self, 'trades'):
                    del self.trades
        else:
            eq = EquityCurve(log_level=self.log_level)
            eq._changes = changes
            eq._times = times
            if keep_trades:
                eq.trades = trades
            return eq
