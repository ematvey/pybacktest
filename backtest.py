import pandas


class MarketData(object):
    class MarketDataValueError(ValueError):
        pass

    OPEN_PRICE_NAMES = ['open', 'Open', 'O', 'o']
    HIGH_PRICE_NAMES = ['high', 'High', 'H', 'h']
    LOW_PRICE_NAMES = ['low', 'Low', 'L', 'l']
    CLOSE_PRICE_NAMES = ['close', 'Close', 'C', 'c']

    def __init__(self, data):
        self.data = data
        self.open_price_column = None
        self.high_price_column = None
        self.low_price_column = None
        self.close_price_column = None
        if isinstance(data, pandas.DataFrame):
            for price in self.OPEN_PRICE_NAMES:
                if price in data.columns:
                    self.open_price_column = price
            for price in self.HIGH_PRICE_NAMES:
                if price in data.columns:
                    self.high_price_column = price
            for price in self.LOW_PRICE_NAMES:
                if price in data.columns:
                    self.low_price_column = price
            for price in self.CLOSE_PRICE_NAMES:
                if price in data.columns:
                    self.close_price_column = price

    @property
    def open(self):
        if self.open_price_column is None:
            raise self.MarketDataValueError('Open price is not found')
        return self.data[self.open_price_column]

    @property
    def high(self):
        if self.high_price_column is None:
            raise self.MarketDataValueError('High price is not found')
        return self.data[self.high_price_column]

    @property
    def low(self):
        if self.low_price_column is None:
            raise self.MarketDataValueError('Low price is not found')
        return self.data[self.low_price_column]

    @property
    def close(self):
        if self.close_price_column is None:
            raise self.MarketDataValueError('Close price is not found')
        return self.data[self.close_price_column]


class BacktestError(Exception):
    pass


def type1_signals_to_positions(signals):
    long_entry = signals.get('long_entry')
    short_entry = signals.get('short_entry')
    long_exit = signals.get('long_exit')
    short_exit = signals.get('short_exit')

    assert long_entry is not None or short_entry is not None
    if long_entry is not None and short_entry is not None:
        assert long_entry.index.equals(short_entry.index)
    if long_entry is not None and long_entry.dtype != bool:
        raise BacktestError("long_entry dtype != bool (use X.astype('bool')")
    if short_entry is not None and short_entry.dtype != bool:
        raise BacktestError("short_entry dtype != bool (use X.astype('bool')")
    if long_exit is not None:
        assert long_exit.index.equals(long_entry.index)
        if long_exit.dtype != bool:
            raise BacktestError("long_exit dtype != bool (use X.astype('bool')")
    if short_exit is not None:
        assert short_exit.index.equals(short_entry.index)
        if short_exit.dtype != bool:
            raise BacktestError("short_exit dtype != bool (use X.astype('bool')")

    p = None
    if long_entry is not None:
        l = pandas.Series(index=long_entry.index, dtype='float')
        l.ix[long_entry] = 1.0
        if long_exit is not None:
            l.ix[long_exit] = 0.0
        if short_entry is not None:
            l.ix[short_entry] = 0.0
        p = l.ffill()
    if short_entry is not None:
        s = pandas.Series(index=long_entry.index, dtype='float')
        s.ix[short_entry] = -1.0
        if short_exit is not None:
            s.ix[short_exit] = 0.0
        if long_entry is not None:
            s.ix[long_entry] = 0.0

        if p is None:
            p = s.ffill()
        else:
            p = p + s.ffill()
    p = p.fillna(value=0.0)
    return p


def type2_signals_to_positions(signals):
    long_pos = signals.get('long')
    short_pos = signals.get('short')
    assert long_pos is not None or short_pos is not None
    p = None
    if long_pos is not None:
        assert long_pos.dtype == bool
        l = pandas.Series(index=long_pos.index, dtype='float')
        l.ix[long_pos] = 1.0
        p = l.fillna(value=0.0)
    if short_pos is not None:
        assert short_pos.dtype == bool
        s = pandas.Series(index=long_pos.index, dtype='float')
        s.ix[short_pos] = -1.0
        if p is None:
            p = s
        else:
            p = p + s.fillna(value=0.0)
    p = p.fillna(value=0.0)
    return p


def execute(price, positions):
    result = pandas.DataFrame()
    trades = positions.diff().fillna(value=0)

    # efficient way to calculate equity curve
    equity_curve = (positions * price) - (trades * price).cumsum()

    # find trade end points
    long_close = (positions <= 0) & (positions > 0).shift()
    short_close = (positions >= 0) & (positions < 0).shift()
    crosspoint = long_close | short_close

    trade_equity = equity_curve[crosspoint].diff().dropna()

    result['equity'] = equity_curve.diff().fillna(value=0)
    result['long_equity'] = trade_equity[long_close]
    result['short_equity'] = trade_equity[short_close]

    return result


def trade_on_current_close(data, positions):
    return execute(data.close, positions)


def trade_on_next_open(data, positions):
    return execute(data.open.shift(-1), positions)


class Backtest(object):
    def __init__(self, data, strategy, name=None, execution=trade_on_current_close):
        self.name = name
        if not isinstance(data, MarketData):
            data = MarketData(data)
        self.data = data
        self.strategy = strategy
        self.signals = signals = strategy(data)
        self.positions = None
        if isinstance(signals, pandas.Series):
            self.positions = signals
        elif isinstance(signals, (dict, pandas.DataFrame)):
            if 'long_entry' in signals or 'short_entry' in signals:
                self.positions = type1_signals_to_positions(signals)
            elif 'long' in signals or 'short' in signals:
                self.positions = type2_signals_to_positions(signals)
        if self.positions is None:
            raise BacktestError('incorrect *signals*')
        self.result = execution(self.data, self.positions)
