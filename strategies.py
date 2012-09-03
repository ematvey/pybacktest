## Core classes for strategies
## order format: (contract, timestamp, limit_price, volume, direction)

import logging
LOGGING_LEVEL = logging.INFO

class Strategy(object):

    def __init__(self, name=None, log_level=None):
        self.orders = []
        if name == None:
            name = self.__class__.__name__
        self.name = name
        self.log = logging.getLogger(self.name)
        self.log.setLevel(log_level or LOGGING_LEVEL)

    def order_callback(self, order):
        """ Order callback should be set by backtester before
            the first `step`. """
        raise NotImplementedError

    def process_datapoint(self, datapoint):
        """ Method for hiding all internal operations, (e.g. tracking prices).
            Backtester calls this before it calls `step`.
            Use `super` when overriding. """
        self.step(datapoint)

    def step(self, datapoint):
        """ Main method, strategy decisions should start here.
        Do not use `super` when overriding. """
        raise NotImplementedError

    def order(self, timestamp, limit_price, volume, direction=None,
      contract=''):
        """ Send order method. """
        if not direction:
            if volume > 0:
                direction = 'buy'
            elif volume < 0:
                direction = 'sell'
        order = (timestamp, limit_price, abs(volume), direction)
        self.orders.append(order)
        self.log.debug('sent order %s', order)
        self.order_callback(order)

class PositionalStrategy(Strategy):

    def __init__(self, name=None, contract='', volume=1.0, slippage=0.):
        '''
        * `slippage` determines assumed transaction costs when using naive
            backtester; when using matching engine backtester, slippage becomes
            actual limit price shift.
        * `volume` determines max size for backtesting. E.g., setting volume=5
            followed by self.change_position(0.5) will yield a buy order with
            volume=2.5.
        * `contract` is not used anywhere at the moment.
        '''
        self.positions = []
        self.contract = contract
        self.volume = volume
        self.slippage = slippage
        self._last = None
        self._timestamp = None
        super(PositionalStrategy, self).__init__(name)

    @property
    def position(self):
        ''' Current position. Always in range [-1, 1]. '''
        return self.positions[-1][2]

    def process_datapoint(self, datapoint):
        timestamp = datapoint.timestamp
        C = datapoint.C
        self._last = C
        self._timestamp = timestamp
        if len(self.positions) == 0: # initial position = 0
            self.positions.append((timestamp, C, 0))
        super(PositionalStrategy, self).process_datapoint(datapoint)

    def change_position(self, position, timestamp=None, price=None):
        if not timestamp:
            timestamp = self._timestamp
        if not price:
            price = self._last
        slip = self.slippage
        old_position = self.position
        volume = position - old_position
        self.positions.append((timestamp, price, position))
        limit_price = price + slip if volume > 0 else price - slip
        self.log.debug('position changed from %s to %s' % (old_position,
          position))
        self.order(timestamp, limit_price, volume)

    ## Convenience methods --------------------------------------------------
    def exit(self, price=None):
        self.change_position(0, price=price)

    def long(self, price=None):
        self.change_position(1, price=price)

    def short(self, price=None):
        self.change_position(-1, price=price)
