'''
 Core classes for strategies
 order format: (timestamp, limit_price, volume, direction)

'''

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
        """ Finalize everything before close, i.e. shut down the position,
            reset indicators, etc."""
        raise NotImplementedError

    def order(self, timestamp, limit_price, volume):
        """ Send order method. """
        order = (timestamp, limit_price, volume)
        self.orders.append(order)
        self.log.debug('sent order %s', order)
        self.order_callback(order)

class PositionalStrategy(Strategy):
    ''' PositionalStrategy will handle all order generation resulting from
        changing its position via `change_posiiton` method. '''

    def __init__(self, name=None, volume=1.0, slippage=0., log_level=None):
        '''
        Initialize PositionalStrategy.

        `slippage` determines assumed transaction costs when using naive
            backtester; when using matching engine backtester, slippage becomes
            actual limit price shift.

        `volume` determines max size for backtesting. E.g., setting volume=5
            followed by self.change_position(0.5) will yield a buy order with
            volume=2.5.

        And do not forget to call the constructor when overriding.
        '''
        self.positions = []
        self.volume = volume
        self.slippage = slippage
        self._current_point = None
        self._first_timestamp = None
        self._price_overrides = 0
        super(PositionalStrategy, self).__init__(name, log_level)

    @property
    def position(self):
        ''' Current position. Always in range [-1, 1]. '''
        return self.positions[-1][2]

    def process_datapoint(self, datapoint):
        ''' Accept `datapoint` and prepare to execute next `step`. '''
        timestamp = datapoint.timestamp
        if self._current_point and self._current_point.timestamp.date() != \
          timestamp.date():
            self._first_timestamp = timestamp
        self._current_point = datapoint
        if len(self.positions) == 0: # initialize position at 0
            self.positions.append((timestamp, datapoint.C, 0))
        super(PositionalStrategy, self).process_datapoint(datapoint)

    def change_position(self, position, price='close', defaulting='open',
                        timestamp=None, ignore_timecheck=False):
        '''
        Change position of strategy, which is the main way to initiate
        trades.

        `position` should be in range [-1, 1]. 1 means `go full long`,
            -1 `go full short`.

        `price` sould be 'close' if entry should by performed on close
            price, or some number if entry should be made by stop order.

        `defaulting` determines a way to resolve stop price
            unavailability: if stop price is not available in current bar,
            execute order by 'open' or 'close' prices, or pass 'override' to
            execute order by requested price regardless.

        `timestamp` is used if you want to double-check if your strategy
            trades on current bar; otherwise, omit it from your args.

        `ignore_timecheck` allows you to bypass timestamp safechecks,
            i.e. when closing the trade on previous EOD from today's first bar.
        '''
        point = self._current_point
        timestamp = timestamp or point.timestamp
        slip = self.slippage
        old_position = self.position
        volume = position - old_position
        if not ignore_timecheck:
            if timestamp != point.timestamp:
                self.log.warning('order timestamp %s is not current '\
                                 'timestamp %s' ,timestamp, point.timestamp)
            if self._first_timestamp == timestamp:
                self.log.warning('position change on the openning of a day')
        ## calculating price
        if price == 'close':
            limit_price = point.C
        elif type(price) in (float, int): # calc limit price from stop price
            # price present in current bar? everything's ok then
            if price >= point.L - slip and price <= point.H + slip:
                limit_price = price
            # price is not in current bar (i.e., gap)? defaulting
            else:
                self._price_overrides += 1
                if defaulting == 'close':
                    limit_price = point.C
                elif defaulting == 'open':
                    limit_price = point.O
                elif defaulting == 'override':
                    pass
                else:
                    raise Exception('requested defaulting mode '\
                                    ' is not supported')
                self.log.debug('requested price %s (%s) is not present in '\
                                'current bar (%s)' % (price, volume, timestamp))
                self.log.debug('defaulting to `%s` price %s', defaulting,
                                 limit_price)
        else:
            raise Exception('requested price %s cannot be accepted' % price)
        ## executing
        self.positions.append((timestamp, limit_price, position))
        if volume > 0:
            limit_price += slip
        elif volume < 0:
            limit_price -= slip
        self.log.debug('position change from %s to %s' % (old_position,
          position))
        self.order(timestamp, limit_price, volume)

    def finalize(self):
        self.log.debug('finalization requested')
        if self.position != 0:
            self.change_position(0)
        self._current_point = None
        self._first_timestamp = None
        self.log.debug('finalized')

    def exit(self, **kwargs):
        self.change_position(0, **kwargs)

    def long(self, **kwargs):
        self.change_position(1, **kwargs)

    def short(self, **kwargs):
        self.change_position(-1, **kwargs)
