import numpy
import pandas
import performance_statistics

import logging
LOGGING_LEVEL = logging.INFO

class TradeError(Exception):
    pass

class EquityCalculator(object):
    ''' Calculates EquityCurve from trades and price changes '''

    def __init__(self, full_curve=None, trades_curve=None, log_level=None):
        self._full_curve = full_curve or EquityCurve()
        self._trades_curve = trades_curve or EquityCurve()
        self._full_curve_merged = EquityCurve()
        self._trades_curve_merged = EquityCurve()
        self.pos = 0
        self.var = 0
        self.now = None
        self.price = None
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level or LOGGING_LEVEL)

    def new_price(self, timestamp, price):
        self.now = timestamp
        self.price = price
        self._full_curve.add_point(timestamp, self.var + self.pos * price)

    def new_trade(self, timestamp, price, volume, direction):
        #if timestamp < self.now:
        #    raise TradeError('Attempting to make trade in the past')
        self.log.debug('trade %s, price %s, volume %s, dir %s' % \
          (timestamp, price, volume, direction))
        if direction == 'sell':
            volume *= -1
        self.var -= price * volume
        self.pos += volume
        equity = self.var + self.pos * price
        diff = equity - sum(self._trades_curve._changes)
        if diff != 0:
            self.log.debug('new equity point %s registered on %s', equity, timestamp)
            self.log.debug('equity change: %s', diff)
        self._trades_curve.add_point(timestamp, equity)
        self._trades_curve.add_trade((timestamp, price, volume))

    def merge(self):
        ''' Record current results and prepare to start calculating equity
            from the scratch. Purpose: to be able to backtest single strategy
            on a whole basket of instruments. '''
        if self.pos != 0:
            raise Exception('Merge requested when position != 0')
        self._full_curve_merged.merge(self._full_curve)
        self._full_curve = EquityCurve()
        self._trades_curve_merged.merge(self._trades_curve)
        self._trades_curve = EquityCurve()
        self.var = 0

    @property
    def full_curve(self):
        if not len(self._full_curve) == 0:
            self.merge()
        return self._full_curve_merged

    @property
    def trades_curve(self):
        if not len(self._trades_curve) == 0:
            self.merge()
        return self._trades_curve_merged


class EquityCurve(object):
    ''' Keeps history of equity changes and calculates various performance
        statistics. Optional: keeps track of trades. '''

    def __init__(self):
        self._changes = []
        self._times = []
        self._cumsum = 0
        self.trades = []

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

    def add_trade(self, trade):
        ''' Add trade. Not used in any computation currently. '''
        self.trades.append(trade)

    def series(self, mode='equity'):
        ''' Pandas TimeSeries object of equity/changes.
        * `mode` determines type, could be "equity" for cumulative equity
           dynamic or "changes" for time series of changes between neighbour
           equity points. '''
        if mode == 'equity':
            return pandas.TimeSeries(data=numpy.cumsum(self._changes),
              index=self._times)
        elif mode == 'changes':
            return pandas.TimeSeries(data=self._changes, index=self._times)
        else:
            raise Exception('Unsupported mode requested during export '\
              'into pandas.TimeSeries')

    def __getitem__(self, stat):
        ''' Calculate statistic `stat` on equity dynamics '''
        if len(self._changes) == 0:
            raise Exception('Cannot calculate statistics on empty EquityCurve')
        s = stat.lower()
        func = getattr(performance_statistics, stat.lower(), None)
        if func:
            return func(numpy.array(self._changes))
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

    def merge(self, curve, overwrite=True):
        ''' Merge two curves. Used for backet testing. Will overwrite self
            unless `overwrite` was set to False.
            Warning: recorded trades will be discarded for self to avoid
            potential confusion. '''
        changes1 = self._changes
        changes2 = curve._changes
        times1 = self._times
        times2 = curve._times
        if len(changes1)==0:
            if overwrite:
                self._changes = curve._changes
                self._times = curve._times
                return
            else:
                return curve
        if len(changes2)==0:
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
        if overwrite:
            self._changes = changes
            self._times = times
            if hasattr(self, 'trades'):
                del self.trades
        else:
            eq = EquityCurve()
            eq._changes = changes
            eq._times = times
            return eq
