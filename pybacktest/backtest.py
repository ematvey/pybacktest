import pandas


class MarketDataValueError(ValueError):
    pass


class MarketData(object):
    OPEN_PRICE_NAMES = ['Open', 'open', 'O', 'o']
    HIGH_PRICE_NAMES = ['High', 'high', 'H', 'h']
    LOW_PRICE_NAMES = ['Low', 'low', 'L', 'l']
    CLOSE_PRICE_NAMES = ['Close', 'close', 'C', 'c']

    def __init__(self, data):
        self.data = data
        self.open_price_column = None
        self.high_price_column = None
        self.low_price_column = None
        self.low_price_column = None
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
            raise MarketDataValueError('Open price is not found')
        return self.data[self.open_price_column]

    @property
    def high(self):
        if self.high_price_column is None:
            raise MarketDataValueError('High price is not found')
        return self.data[self.high_price_column]

    @property
    def low(self):
        if self.low_price_column is None:
            raise MarketDataValueError('Low price is not found')
        return self.data[self.low_price_column]

    @property
    def close(self):
        if self.close_price_column is None:
            raise MarketDataValueError('Close price is not found')
        return self.data[self.close_price_column]


class BacktestError(Exception):
    pass


EXECUTION_NEXT_OPEN = 'next-open'
EXECUTION_CURRENT_CLOSE = 'current-close'

LONG_KEYS = ['long', 'long_entry', 'buy']
LONG_EXIT_KEYS = ['long_exit', 'sell']
SHORT_KEYS = ['short', 'short_entry']
SHORT_EXIT_KEYS = ['short_exit', 'cover']


def _chained_get(container, chain):
    for key in chain:
        value = container.get(key)
        if value is not None:
            return value


def process_signals(long_entry, short_entry, long_exit, short_exit):
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


def parse_signals(signals):
    long_entry = _chained_get(signals, LONG_KEYS)
    short_entry = _chained_get(signals, SHORT_KEYS)
    long_exit = _chained_get(signals, LONG_EXIT_KEYS)
    short_exit = _chained_get(signals, SHORT_EXIT_KEYS)
    assert long_entry or short_entry
    if long_entry and short_entry:
        assert long_entry.index.equal(short_entry.index)
    if long_entry and long_entry.dtype != bool:
        raise BacktestError("long_entry dtype != bool (use .astype('bool')")
    if short_entry and short_entry.dtype != bool:
        raise BacktestError("short_entry dtype != bool (use .astype('bool')")
    if long_exit:
        assert long_exit.index.equal(long_entry.index)
        if long_exit.dtype != bool:
            raise BacktestError("long_exit dtype != bool (use .astype('bool')")
    if short_exit:
        assert short_exit.index.equal(short_entry.index)
        if short_exit.dtype != bool:
            raise BacktestError("short_exit dtype != bool (use .astype('bool')")
    return long_entry, short_entry, long_exit, short_exit


class BacktestResult(object):
    def __init__(self, name, data, signals, execution_style):
        self.name = name
        self.data = MarketData(data)
        self.signals = signals
        self.execution_style = execution_style

        self.positions = None
        if isinstance(signals, pandas.Series):
            self.positions = signals
        elif isinstance(signals, (dict, pandas.DataFrame)):
            if 'positions' in signals.columns:
                self.positions = signals['positions']
            else:
                self.positions = process_signals(*parse_signals(signals))
        else:
            raise BacktestError()

        self.trades = self.positions.diff()


class Backtest(object):
    def __init__(self, name=None, spec=None):
        self.name = name
        self.instruments = {}
        self.signals = {}

        if spec is not None:
            for backtest in spec:
                self.backtest(**backtest)

    def backtest(self, ticker, data, signals):
        if not set(data.index).issuperset(signals.index):
            raise BacktestError('Signals index must be subset of Data index')
        self.instruments[ticker] = MarketData(data)
        self.signals[ticker] = signals
