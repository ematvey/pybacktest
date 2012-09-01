
import logging
import equity

logging.basicConfig()
LOGGING_LEVEL = logging.DEBUG

# specifies current data abstraction
get_price = lambda datapoint: datapoint.O
get_time = lambda datapoint: datapoint.timestamp


class Backtester(object):
    ''' Backtester base class '''
    
    def __init__(self, strategy, data, run=True):
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
        self.log.setLevel(LOGGING_LEVEL)
        calc = self._equity_calc = equity.EquityCalculator()
        self.results = {'full equity curve': calc.full_curve, 
                        'equity curve by trades': calc.trades_curve}
    
    def run(self):
        self.log.info('backtest started')
        for datapoint in self.data:
            self._equity_calc.new_price(get_time(datapoint), 
              get_price(datapoint))
            self.strategy.process_datapoint(datapoint)
        self.log.info('backtest complete; results are in self.results')
    
    def _matching_callback(self, order):
        ''' Order is assumed to be (timestamp, limit_price, volume, direction)
            tuple. '''
        NotImplementedError
    
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
