import re

import pandas

t_open = 'open'
t_high = 'high'
t_low = 'low'
t_close = 'close'
t_price = 'price'
t_trade_price = 'trade_price'

t_l = 'long'
t_s = 'short'
t_l_en = 'long_entry'
t_s_en = 'short_entry'
t_l_ex = 'long_exit'
t_s_ex = 'short_exit'

type1_signal_tokens = [t_l_en, t_s_en]
type2_signal_tokens = [t_l, t_s]

t2_signal_tokens = [t_l, t_s]
t1_signal_tokens = [t_l_en, t_s_en, t_l_ex, t_s_ex]
signal_tokens = t1_signal_tokens + t2_signal_tokens

price_tokens = [t_trade_price, t_price, t_open, t_high, t_low, t_close]


class SignalError(Exception):
    pass


class MixedSignalsError(SignalError):
    pass


def format_field(symbol, token, group):
    p = token
    if symbol is not None:
        p = symbol + '_' + p
    if group is not None:
        p = p + '_' + group
    return p


signal_re = re.compile(
    '^(?:(?P<symbol>[a-zA-Z0-9]+)_)?(?P<token>(?:%s))(?:_(?P<group>[a-zA-Z0-9]+))?$' % (
        '|'.join(signal_tokens + price_tokens)
    ))


def exrem(series):
    # series.ix[series == series.shift()] = numpy.nan
    return series


def insert(pos_arr, price_arr, size, entry, exit, opposite_entry, trade_price):
    def _set(_sel, _size):
        pos_arr.ix[_sel] = _size
        price_arr.ix[_sel] = trade_price.ix[_sel]

    if entry is not None:
        _set(entry, size)
    if exit is not None:
        _set(exit, 0)
    if opposite_entry is not None:
        _set(opposite_entry, 0)


def type1_partial(signals, trade_price, longpos_arr=None, shortpos_arr=None, price_arr=None):
    long_entry = signals.get(t_l_en)
    short_entry = signals.get(t_s_en)
    long_exit = signals.get(t_l_ex)
    short_exit = signals.get(t_s_ex)

    insert(longpos_arr, price_arr, 1.0, long_entry, long_exit, short_entry, trade_price)
    insert(shortpos_arr, price_arr, -1.0, short_entry, short_exit, long_entry, trade_price)

    return longpos_arr, shortpos_arr, price_arr


def type2_to_type1(signals):
    _long = signals.get(t_l)
    _short = signals.get(t_s)
    s = {}

    def enex(series):
        d = series.diff()
        d.ix[0] = series.ix[0]
        en = d > d.shift()
        en.ix[0] = d.ix[0] > 0
        ex = d < d.shift()
        ex.ix[0] = d.ix[0] < 0
        return en.astype('bool'), ex.astype('bool')

    if _long is not None:
        s['long_entry'], s['long_exit'] = enex(_long)

    if _short is not None:
        s['short_entry'], s['short_exit'] = enex(_short)

    return s


class SymbolSignalBox(object):
    def __init__(self, symbol):
        self.index = None
        self._signals = {}
        self._trade_prices = {}
        self.symbol = symbol
        self.type = None

    def _mixed(self):
        raise MixedSignalsError(
            'cannot mix type 1 (long/short entry/exit) and type 2 (long/short) signals within one symbol')

    @property
    def groups(self):
        return set(self._signals.keys())

    def _try_add_signal(self, value, token, group):
        if self.index is not None:
            if not value.index.equals(self.index):
                raise SignalError('one or more of the signals have different index')

        if token in t1_signal_tokens:
            if self.type is not None and self.type != 1:
                self._mixed()
            self.type = 1
        elif token in t2_signal_tokens:
            if self.type is not None and self.type != 2:
                self._mixed()
            self.type = 2
        else:
            return False

        if value.dtype != bool:
            raise SignalError("signal %s has non-bool dtype (use X.astype('bool')" % ((self.symbol, token, group),))

        if group not in self._signals:
            self._signals[group] = {}
        self._signals[group][token] = value
        if self.index is None:
            self.index = value.index

        return True

    def _try_add_price(self, value, token, group):
        if token == t_trade_price:
            self._trade_prices[group] = value
            return True
        return False

    def add(self, value, token, group):
        assert isinstance(value, pandas.Series)
        if not self._try_add_signal(value, token, group):
            if not self._try_add_price(value, token, group):
                raise SignalError('Cannot process Signal token: %s' % token)

    def __iter__(self):
        # TODO: order of resolution between signal groups might be important, pay attention to it
        # need to sort it
        for group, signals in self._signals.items():
            try:
                price = self._trade_prices.get(group)
                if price is None:
                    price = self._trade_prices[None]
            except KeyError:
                raise SignalError(
                    'trade price for symbol `%s` / signal group `%s` is not specified' % (self.symbol, group))
            yield group, signals, price


class Signals(object):
    def __init__(self, signals):
        self.raw_signals = signals
        self._signals = {}
        self.multiple_assets = None

        for column, value in self.raw_signals.items():
            m = signal_re.match(column)
            if m is None:
                raise SignalError('Unkown Signal format: %s' % column)
            symbol, token, group = m.groups()
            self._add(value, symbol=symbol, token=token, group=group)

    def _mixed(self):
        raise MixedSignalsError('cannot mix multi- and single-asset signals in one backtest')

    def _add(self, value, token, symbol=None, group=None):
        if not isinstance(token, str):
            raise SignalError()

        if self.multiple_assets is None:
            if symbol is None:
                self.multiple_assets = False
            else:
                self.multiple_assets = True
        else:
            if symbol is None and self.multiple_assets is True:
                self._mixed()
            if symbol is not None and self.multiple_assets is False:
                self._mixed()

        if symbol not in self._signals:
            self._signals[symbol] = SymbolSignalBox(symbol)
        self._signals[symbol].add(value, token, group)

    def __iter__(self):
        for symbol, signals in self._signals.items():
            yield symbol, signals

    def symbols(self):
        return set(self._signals.keys())


class ExecutionError(ValueError):
    pass


class Execution(object):
    """
    ExecutionIterator allows for iteration over Signals and execution Prices, respecting different symbols, groups,
    and prices.

    Iterator signature: symbol, group, price, signals
    """

    def __init__(self, data, signals):
        self.signals = Signals(signals)

    def produce_results(self):
        for symbol, signals in self.signals:
            longsig_arr = pandas.Series(index=signals.index, dtype='float')
            shortsig_arr = pandas.Series(index=signals.index, dtype='float')
            price_arr = pandas.Series(index=signals.index, dtype='float')

            ss = {}
            for group, group_signals, group_price in signals:
                ss.update({symbol + '_' + k + '_' + str(group): v for k, v in group_signals.items()})
                s = group_signals
                for k, v in group_signals.items():
                    print(symbol, group, k)
                    print(v.head(5))
                if signals.type == 1:
                    pass
                elif signals.type == 2:
                    print('tconv')
                    s = type2_to_type1(group_signals)
                else:
                    raise SignalError('WTF: signal type %s' % signals.type)
                print(s.keys())
                type1_partial(s, group_price, longsig_arr, shortsig_arr, price_arr)
                for k, v in group_signals.items():
                    print(symbol, group, k)
                    print(v.head(5))

            longpos_arr = longsig_arr.ffill().fillna(value=0)
            shortpos_arr = shortsig_arr.ffill().fillna(value=0)

            df = pandas.DataFrame(dict(price=price_arr, longpos=longsig_arr, shortpos=shortsig_arr))
            df = pandas.concat([df, pandas.DataFrame(ss)], axis=1)

            yield symbol, df
