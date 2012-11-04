import equity

import copy
import logging
LOGGING_LEVEL = logging.INFO


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

        * `data` should be ab iterable over datapoints or over iterables over
            datapoints (in case you're doing portfolio testing, e.g. on futures
            chain.

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
        self.data = data if hasattr(data[0], '__iter__') else [data]
        self.trades = []
        self.log = logging.getLogger(self.__class__.__name__)
        self.log_level = log_level or LOGGING_LEVEL
        self.log.setLevel(self.log_level)
        calc = self._equity_calc = equity.EquityCalculator(log_level=log_level)
        self.full_curve = calc.full_curve
        self.trades_curve = calc.trades_curve
        if run:
            self.run()

    def run(self):
        self.log.info('backtest started')
        for dataset in self.data:
            s = self.strategy_class(#log_level=self.log_level,
                                    *self.strategy_args,
                                    **self.strategy_kwargs)
            s.order_callback = self._matching_callback
            for datapoint in dataset:
                self._current_point = datapoint
                ### NOTE: datapoint is assumed to have `C` attr
                ## change next string if your data is represented in other
                ## way
                self._equity_calc.new_price(datapoint.timestamp, datapoint.C)
                s.process_datapoint(datapoint)
            s.finalize()
            self._equity_calc.merge()
        self.log.info('backtest complete; results are in self.results')

    def _matching_callback(self, order):
        ''' Match order from Strategy.
            Order is assumed to be (timestamp, limit_price, volume)
            tuple. '''
        raise NotImplementedError

    def _trade(self, timestamp, price, volume):
        ''' Accept trades trades from `_matching_callback` or other
            matching engine. '''
        cp = self._current_point
        if price > cp.H or price < cp.L:
            self.log.error('requested trade price %s is not available '\
                           'in bar %s (H %s L %s)', price, cp.timestamp,
                           cp.H, cp.L)
        self._equity_calc.new_trade(timestamp, price, volume)


class SimpleBacktester(Backtester):
    ''' Backtester which assumes that it is possible to execute all orders
        at their requested prices; thus, `limit_price` of orders should
        account for expected slippage. '''

    def _matching_callback(self, order):
        self._trade(*order)
