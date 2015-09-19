import numpy
import pandas


class BacktestError(Exception):
    pass


def dummy_signals_to_positions(signals):
    return signals


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


def select_signal_extractor(signals):
    """ Create singal-to-position converter function
    """
    if isinstance(signals, pandas.Series):

        # option 1: positions
        return dummy_signals_to_positions

    elif isinstance(signals, (dict, pandas.DataFrame)):

        # option 2: full spec with entries/exists (type 1 signals)
        if 'long_entry' in signals or 'short_entry' in signals:
            return type1_signals_to_positions

        # option 3: separate long/short positions (type 2 signals)
        elif 'long' in signals or 'short' in signals:
            return type2_signals_to_positions


def fast_execute(price, positions):
    """ Fast vectorized execute. Works with standard position/fixed-price
        market order entries, but not with conditional trades like stops or
        limit orders.
    """
    # find trade end points
    long_close = (positions <= 0) & (positions > 0).shift()
    short_close = (positions >= 0) & (positions < 0).shift()
    crosspoint = long_close | short_close
    crosspoint[0] = True

    # efficient way to calculate equity curve
    returns_at_crosspoints = price[crosspoint].pct_change().dropna()

    result = pandas.DataFrame()
    result['equity'] = (price.pct_change() * positions.shift())
    result['long_equity'] = returns_at_crosspoints[long_close]
    result['short_equity'] = -returns_at_crosspoints[short_close]
    return result.fillna(value=0)


def trade_on_current_close(data, positions):
    return fast_execute(data['close'], positions)


def trade_on_next_close(data, positions):
    return fast_execute(data['close'].shift(-1), positions)


def trade_on_next_open(data, positions):
    return fast_execute(data['open'].shift(-1), positions)


class Backtest(object):
    def __init__(self, data, strategy, name=None, execution=trade_on_current_close, extractor=None):
        self.name = name
        self.data = data

        if callable(strategy):
            self.signals = strategy(data)
        else:
            self.signals = strategy

        if extractor is None:
            extractor = select_signal_extractor(self.signals)
        self.positions = extractor(self.signals)

        if self.positions is None:
            raise BacktestError('incorrect *signals*')
        self.result = execution(self.data, self.positions)
