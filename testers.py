import equity

import logging
LOGGING_LEVEL = logging.INFO


class Backtester(object):
    ''' Backtester base class '''

    def __init__(self, strategy, data, run=True, log_level=None):
        '''
        * `strategy` should be Strategy-compatible object, i.e. has
            `process_datapoint` method that accepts datapoints and abstract
            `order_callback` method that accepts
            (contract, timestamp, limit_price, volume, direction)
            formatted orders.
        * `data` should be DataContainer-compatible object, i.e. should be
            an iterable that generates datapoints (assumed to be bar or tick
            objects).
        '''
        self.strategy = strategy
        self.strategy.order_callback = self._matching_callback
        self.data = data
        self.trades = []
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level or LOGGING_LEVEL)
        calc = self._equity_calc = equity.EquityCalculator(log_level=log_level)
        self.full_curve = calc.full_curve
        self.trades_curve = calc.trades_curve
        if run:
            self.run()

    def run(self):
        self.log.info('backtest started')
        for dataset in self.data:
            for datapoint in dataset:
                self._current_point = datapoint
                self._equity_calc.new_price(datapoint.timestamp, datapoint.C)
                self.strategy.process_datapoint(datapoint)
            self.strategy.finalize()
            self._equity_calc.merge()
        self.log.info('backtest complete; results are in self.results')

    def _matching_callback(self, order):
        ''' Match order from Strategy.
            Order is assumed to be (timestamp, limit_price, volume, direction)
            tuple. '''
        raise NotImplementedError

    def _trade(self, timestamp, price, volume, direction):
        self.log.debug('trade %s, price %s, volume %s' % \
          (timestamp, price, volume))
        cp = self._current_point
        if price > cp.H or price < cp.L:
            self.log.error('requested trade price %s is not available '\
                           'in bar %s (H %s L %s)', price, cp.timestamp,
                           cp.H, cp.L)
        self._equity_calc.new_trade(timestamp, price, volume, direction)


class SimpleBacktester(Backtester):
    ''' Backtester which assumes that it is possible to execute all orders
        for their requested prices; thus, `limit_price` of orders should
        account for expected slippage. '''

    def _matching_callback(self, order):
        self.log.debug('recieved order %s', order)
        self._trade(*order)
