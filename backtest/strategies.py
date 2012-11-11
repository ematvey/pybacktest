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
        if log_level:
            self.log.setLevel(log_level)
        self.log_level = log_level

    def order_callback(self, order):
        """ Order callback should be set by backtester before
            the first `step`. """
        raise NotImplementedError

    def process_data(self, data):
        """ Method for hiding all internal operations, (e.g. tracking prices).
            Backtester calls this before it calls `step`.
            Use `super` when overriding. """
        self.step(data)

    def step(self, data):
        """ Main method, strategy decisions should start here.
            Do not use `super` when overriding.
            `data` could be any object - dict, tuple, list, singleton object -
            just make sure that strategy knows what datatype to expect. """
        raise NotImplementedError

    def finalize(self):
        """ Finalize everything before close, i.e. shut down the position,
            reset indicators, etc. """
        raise NotImplementedError

    def order(self, timestamp, limit_price, volume, instrument=None):
        """ Send order method. Optional `instrument` argument is
            required if running multi-asset backtest. """
        if instrument:
            order = (timestamp, limit_price, volume, instrument)
        else:
            order = (timestamp, limit_price, volume)
        self.orders.append(order)
        self.log.debug('sent order %s', order)
        self.order_callback(order)


class PositionalStrategy(Strategy):
    ''' PositionalStrategy will handle all order generation resulting from
        changing its position via `change_posiiton` method.

        Strategy will infer single/multi asset backtest mode from first
        datapoint it recieves.

        In multi-asset backtest:
            self.change_position, self.long, self.short, self.exit from now on
            will require `instrument` argument set and self.position will return
            dict of positions on all traded instruments. You dont need to set
            List of positions explicitly, just `change_position` on them and it
            will be recorded.
    '''

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
        self.volume = volume
        self.slippage = slippage
        self._price_overrides = 0
        super(PositionalStrategy, self).__init__(name=name, 
                                                 log_level=log_level)

    @property
    def position(self):
        ''' Current position(s). Always in range [-1, 1]. '''
        if not self.multi:
            return self.positions[-1][2]
        else:
            return dict([(k, v[-1][2]) for k, v in self.positions.iteritems()])

    def process_data(self, data):
        '''
        Process `data` and prepare to execute next `step`.

        `data` is assumed to be one of the following:

        a) single OHLC bar with associated timestamp in corresponding
        attributes, e.g. data = <bar>;

        c) dict, with instrument names in keys and OHCL-likes in values, e.g.
        data = {'S&P500': <bar>, 'EURUSD': <bar>}

        Using a) assumes single-asset backtest, using b) assumes
        multi-asset backtest.

        '''
        if not hasattr(self, 'multi'):
            self.multi = type(data) == dict
            if not self.multi:
                self._current_point = None
                self._first_timestamp = None
                self.positions = []
            else:
                self._current_point = {}
                self._first_timestamp = {}
                self.positions = {}
        if not self.multi:
            datapoint = data
            timestamp = datapoint.timestamp
            if self._current_point and self._current_point.timestamp.date() != \
               timestamp.date():
                self._first_timestamp = timestamp
            self._current_point = datapoint
            if len(self.positions) == 0: # initialize position at 0
                self.positions.append((timestamp, datapoint.C, 0))
        else:
            for k, v in data.iteritems():
                datapoint = v
                cp = self._current_point.setdefault(k, None)
                self.positions.setdefault(
                    k, [(datapoint.timestamp, datapoint.C, 0)])
                if cp and cp.timestamp.date() != datapoint.timestamp.date():
                    self._first_timestamp[k] = datapoint.timestamp
                self._current_point[k] = datapoint
        super(PositionalStrategy, self).process_data(data)

    def change_position(self, position, instrument=None, price='close',
                        defaulting='open', timestamp=None,
                        ignore_timecheck=False):
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
        assert instrument or not self.multi, \
           'Changing position requires instrument when multi-backtesting'
        point = self._current_point if not self.multi else \
                self._current_point.get(instrument)
        if not point:
            raise Exception('Wrong instrument requested')
        timestamp = timestamp or point.timestamp
        slip = self.slippage
        old_position = self.position if not self.multi else \
                       self.position[instrument]  # if we got here,
                                                  # position should be
                                                  # present
        volume = position - old_position
        if not ignore_timecheck:
            if timestamp != point.timestamp:
                self.log.warning('order timestamp %s is not current '\
                                 'timestamp %s' ,timestamp, point.timestamp)
            #if self._first_timestamp == timestamp:
            #    self.log.warning('position change on the openning of a day')
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
        if not self.multi:
            self.positions.append((timestamp, limit_price, position))
        else:
            self.positions[instrument].append((timestamp, limit_price, position))
        if volume > 0:
            limit_price += slip
        elif volume < 0:
            limit_price -= slip
        self.log.debug('position change from %s to %s' % (old_position,
          position))
        self.order(timestamp, limit_price, volume, instrument)

    def finalize(self):
        self.log.debug('finalization requested')
        if not self.multi:
            if self.position != 0:
                self.change_position(0)
            self._current_point = None
            self._first_timestamp = None
            self.positions = []
        else:
            for i in self.positions.keys():
                self.change_position(0, instrument=i)
            self._current_point = {}
            self._first_timestamp = {}
            self.positions = {}
        self.log.debug('finalized')

    def exit(self, **kwargs):
        self.change_position(0, **kwargs)

    def long(self, **kwargs):
        self.change_position(1, **kwargs)

    def short(self, **kwargs):
        self.change_position(-1, **kwargs)
