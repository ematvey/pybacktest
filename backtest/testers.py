import equity

import copy
import logging


class Backtester(object):
    ''' Backtester base class '''

    def __init__(self, data, strategy_class,
                 strategy_args=tuple(), strategy_kwargs=dict(),
                 run=True, log_level=None):
        '''
        Arguments
        ----

        * `strategy` should be Strategy class, i.e. has
            `process_datapoint` method that accepts datapoints and abstract
            `order_callback` method that accepts (contract, timestamp,
            limit_price, volume) formatted orders.

        * `strategy_args`, `strategy_kwargs` - arguments for Strategy
            instantiation, specific for each strategy.

        * `data` - possible structures:

          a) Sequence of datapoints, for simple 1-asset backtest:

               [datapoint1, datapoint2, ..., datapointN]

          b) Sequence of dicts, containing datapoints for multiple instruments,
             for multi-asset backtest:

               [{'instrument_1': datapoint1_i1,
                 'instrument_2': datapoint1_i2}, ...]

          You can also pass iterable over a) or b) to test on multiple
          periods combined (e.g. on futures chain).

          Note that datapoints are assumed to have `C` and `timestamp`
          attributes (PositionalStrategy makes some additional assumptions).
          You can change that by slightly adjusting `Backtester` class and used
          Strategy classes.

          If you need to pass some non-standard data to strategies, just attach
          them as attributes to datapoints when preparing your data.

        Important attributes
        ----

        `full_curve` is an EquityCurve that tracks equity changes on every
            datapoint.

        `trades_curve` is an EquityCurve that tracks equity changes only on
            trades.

        '''
        self.strategy_class = strategy_class
        self.strategy_args = strategy_args
        self.strategy_kwargs = strategy_kwargs
        self.data = data if hasattr(data[0], '__iter__') and not type(data[0]) == dict else [data]
        self.multi = True if type(self.data[0][0]) == dict else False
        self.log = logging.getLogger(self.__class__.__name__)
        if log_level:
            self.log.setLevel(log_level)
        self.log_level = log_level
        if not self.multi:
            calc = self._equity = equity.EquityCalculator()
            self._current_point = None
            self.full_curve = calc.full_curve
            self.trades_curve = calc.trades_curve
        else:
            self._equity = {}
            self._current_point = {}
            self.full_curve = equity.EquityCurve(log_level=self.log_level)
            self.trades_curve = equity.EquityCurve(log_level=self.log_level)
        if run:
            self.run()

    def run(self):
        self.log.info('backtest started')
        self.log.info('%s-asset mode', 'single' if self.multi else 'multi')
        for dataset in self.data:
            s = self.strategy_class(log_level=self.log_level,
                                    *self.strategy_args,
                                    **self.strategy_kwargs)
            #assert s.multi == self.multi, \
            #    'strategy and backtester have different asset modes'
            s.order_callback = self._matching_callback
            for datapoint in dataset:
                ### NOTE: datapoint is assumed to have `C` attr
                ## change next string if your data is represented in other
                ## way
                if not self.multi:
                    self._current_point = datapoint
                    self._equity.new_price(datapoint.timestamp, datapoint.C)
                else:
                    for k, v in datapoint.iteritems():
                        self._current_point[k] = v
                        self._equity.setdefault(
                            k, equity.EquityCalculator()
                        ).new_price(v.timestamp, v.C)
                s.process_data(datapoint)
            s.finalize()
            if not self.multi:
                self._equity.merge()
            else:
                for e in self._equity.values():
                    e.merge()
        if self.multi:
            for e in self._equity.values():
                self.trades_curve.merge(e.trades_curve)
                self.full_curve.merge(e.full_curve)
        self.log.info('backtest complete')
        self.log.info('see `trades_curve`, `full_curve` for aggregated curves')
        if self.multi:
            self.log.info('see results on individual instruments in `_equity`')

    def _matching_callback(self, order):
        ''' Match order from Strategy.
            Order is assumed to be (timestamp, limit_price, volume)
            tuple. '''
        raise NotImplementedError

    def _trade(self, timestamp, price, volume, instrument=None):
        ''' Accept trades from `_matching_callback` or other
            matching engine. '''
        assert instrument or not self.multi, \
            'Instrument required when multi-backtesting'
        if self.multi:
            assert instrument in self._current_point and \
                instrument in self._equity, 'Wrong instrument'
        cp = self._current_point if not self.multi else self._current_point[instrument]
        eq = self._equity if not self.multi else self._equity[instrument]
        if price > cp.H or price < cp.L:
            self.log.error('requested trade price %s is not available '\
                           'in bar %s (H %s L %s)', price, cp.timestamp,
                           cp.H, cp.L)
        eq.new_trade(timestamp, price, volume)


class SimpleBacktester(Backtester):
    ''' Backtester which assumes that it is possible to execute all orders
        at their requested prices; thus, `limit_price` of orders should
        account for expected slippage. '''

    def _matching_callback(self, order):
        self._trade(*order)
