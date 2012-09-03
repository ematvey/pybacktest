import numpy
import pandas
import performance_statistics

class TradeError(Exception):
    pass

class EquityCalculator(object):
    ''' Calculates EquityCurve from trades and price changes '''

    def __init__(self, full_curve=None, trades_curve=None):
        self._full_curve = full_curve or EquityCurve()
        self._trades_curve = trades_curve or EquityCurve()
        self._full_curve_merged = EquityCurve()
        self._trades_curve_merged = EquityCurve()
        self.pos = 0
        self.var = 0
        self.now = None

    def new_price(self, timestamp, price):
        self.now = timestamp
        self._full_curve.add_point(timestamp, self.var + self.pos * price)

    def new_trade(self, timestamp, price, volume, direction):
        if timestamp < self.now:
            raise TradeError('Attempting to make trade in the past')
        if direction == 'sell':
            volume *= -1
        self.var -= price * volume
        self.pos += volume
        equity = self.var + self.pos * price
        self._trades_curve.add_point(timestamp, equity)
        self._trades_curve.add_trade((timestamp, price, volume))

    def merge(self):
        ''' Record current results and prepare to start calculating equity
            from the scratch. Purpose: to be able to backtest single strategy
            on a whole basket of instruments. '''
        self._full_curve_merged.merge(self._full_curve)
        self._full_curve = EquityCurve()
        self._trades_curve_merged.merge(self._trades_curve)
        self._trades_curve = EquityCurve()

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
        ''' Pandas TimeSeries object of equity '''
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

    def statistics(self, mode='full'):
        ''' Calculate all possible statistics, as specified in
            `performance_statistics` '''
        if mode == 'full':
            return dict((k, self[k]) for k in performance_statistics.full)
        else:
            raise Exception('Unsupported `mode` of statistics request')

    def merge(self, curve):
        ''' Merge two curves (by diffs). Used for backet testing.
            Warning: recorded trades will be discarded for self to avoid
            potential confusion. '''
        s = self.series(mode='changes').add(curve.series(mode='changes'),
          fill_value=0)
        self._changes = list(s.values)
        self._times = list(s.index)
        if hasattr(self, 'trades'):
            del self.trades
