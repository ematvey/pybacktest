import equity

import logging
LOGGING_LEVEL = logging.INFO


# Specifications for used data abstraction; see 'data.py' for exacts
class DatapointError(AttributeError):
    pass

def get_price(datapoint):
    try:
        return getattr(datapoint, 'O', getattr(datapoint, 'price',
          getattr(datapoint, 'C')))
    except AttributeError:
        raise DatapointError('No `O`/`price`/`C` attribute in Datapoint %s' % \
          datapoint)

def get_time(datapoint):
    try:
        return datapoint.timestamp
    except AttributeError:
        raise DatapointError('No `timestamp` attribute in Datapoint %s' % \
          datapoint)


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
        self.results = {'full': calc.full_curve,
                        'trades': calc.trades_curve}
        if run:
            self.run()

    def run(self):
        self.log.info('backtest started')
        for dataset in self.data:
            for datapoint in dataset:
                self._equity_calc.new_price(get_time(datapoint),
                  get_price(datapoint))
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
        self._equity_calc.new_trade(timestamp, price, volume, direction)


class SimpleBacktester(Backtester):
    ''' Backtester which assumes that it is possible to execute all orders
        for their requested prices; thus, `limit_price` of orders should
        account for expected slippage. '''

    def _matching_callback(self, order):
        self.log.debug('recieved order %s', order)
        self._trade(*order)
