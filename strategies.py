## Core classes for strategies
## order format: (timestamp, limit_price, volume, direction)

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

    def finalize(self):
        """ Finalize everything before close, i.e. shut down the position. """
        raise NotImplementedError

    def order(self, timestamp, limit_price, volume, direction=None):
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

    def __init__(self, name=None, volume=1.0, slippage=0., log_level=None):
        '''
        * `slippage` determines assumed transaction costs when using naive
            backtester; when using matching engine backtester, slippage becomes
            actual limit price shift.
        * `volume` determines max size for backtesting. E.g., setting volume=5
            followed by self.change_position(0.5) will yield a buy order with
            volume=2.5.
        '''
        self.positions = []
        self.volume = volume
        self.slippage = slippage
        self._last = None
        self._timestamp = None
        self._first_timestamp = None
        super(PositionalStrategy, self).__init__(name, log_level)

    @property
    def position(self):
        ''' Current position. Always in range [-1, 1]. '''
        return self.positions[-1][2]

    def process_datapoint(self, datapoint):
        timestamp = datapoint.timestamp
        C = datapoint.C
        if self._timestamp and self._timestamp.date() != timestamp.date():
            self._first_timestamp = timestamp
        self._last = C
        self._timestamp = timestamp
        if len(self.positions) == 0: # initial position = 0
            self.positions.append((timestamp, C, 0))
        super(PositionalStrategy, self).process_datapoint(datapoint)

    def change_position(self, position, timestamp=None, price=None):
        if self._first_timestamp == timestamp:
            self.log.warning("position change on the openning of a day")
        if not timestamp:
            timestamp = self._timestamp
        if not price:
            price = self._last
        slip = self.slippage
        old_position = self.position
        volume = position - old_position
        self.positions.append((timestamp, price, position))
        limit_price = price + slip if volume > 0 else price - slip
        self.log.debug('position change : %s -> %s' % (old_position,
          position))
        self.order(timestamp, limit_price, volume)

    def finalize(self):
        self.log.debug('finalization requested')
        if self.position != 0:
            self.change_position(0)
        self.log.debug('finalized')

    ## Convenience methods --------------------------------------------------
    def exit(self, price=None, timestamp=None):
        self.change_position(0, price=price, timestamp=timestamp)

    def long(self, price=None, timestamp=None):
        self.change_position(1, price=price, timestamp=timestamp)

    def short(self, price=None, timestamp=None):
        self.change_position(-1, price=price, timestamp=timestamp)
