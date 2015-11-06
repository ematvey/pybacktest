import pandas

from pybacktest.execute_defs import *


def dummy_signals_to_positions(signals):
    return signals


def type1_signals_to_positions(signals, symbol=None):
    prefix = ''
    if symbol:
        prefix = symbol + '_'

    long_entry = signals.get(prefix + t_l_en)
    short_entry = signals.get(prefix + t_s_en)
    long_exit = signals.get(prefix + t_l_ex)
    short_exit = signals.get(prefix + t_s_ex)

    assert long_entry is not None or short_entry is not None
    if long_entry is not None and short_entry is not None:
        assert long_entry.index.equals(short_entry.index)
    if long_entry is not None and long_entry.dtype != bool:
        raise SignalError("long_entry dtype != bool (use X.astype('bool')")
    if short_entry is not None and short_entry.dtype != bool:
        raise SignalError("short_entry dtype != bool (use X.astype('bool')")
    if long_exit is not None:
        assert long_exit.index.equals(long_entry.index)
        if long_exit.dtype != bool:
            raise SignalError("long_exit dtype != bool (use X.astype('bool')")
    if short_exit is not None:
        assert short_exit.index.equals(short_entry.index)
        if short_exit.dtype != bool:
            raise SignalError("short_exit dtype != bool (use X.astype('bool')")

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
        s = pandas.Series(index=short_entry.index, dtype='float')
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


def type2_signals_to_positions(signals, symbol=None):
    prefix = ''
    if symbol:
        prefix = symbol + '_'

    long_pos = signals.get(prefix + t_l)
    short_pos = signals.get(prefix + t_s)
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


def signals_to_positions(signals):
    """ Process signals to get positions using different signal-to-positions processing modes

        Supports only conditionless execution
    """
    if isinstance(signals, pandas.Series):
        # option 1: positions
        return signals

    elif isinstance(signals, (dict, pandas.DataFrame)):

        positions = {}

        columns = []
        if isinstance(signals, dict):
            columns = signals.keys()
        elif isinstance(signals, pandas.DataFrame):
            columns = signals.columns

        # option 2: full spec with entries/exists (type 1 signals)
        for column in columns:
            for field in type1_signal_tokens:
                if column.endswith(field):
                    symbol = column.replace(field, '').rstrip('_')
                    if symbol not in positions:
                        p = type1_signals_to_positions(signals, symbol=symbol)
                        if symbol == '':
                            return p
                        positions[symbol] = p

        # option 3: separate long/short positions (type 2 signals)
        for column in columns:
            for field in type2_signal_tokens:
                if column.endswith(field):
                    symbol = column.replace(field, '').rstrip('_')
                    if symbol not in positions:
                        p = type2_signals_to_positions(signals, symbol=symbol)
                        if symbol == '':
                            return p
                        positions[symbol] = p

        if len(positions) > 0:
            return pandas.DataFrame(positions)

    raise SignalError('signals are in unknown form, cannot select processor')


def vectorized_execute_one(trade_price, positions):
    """ Fast vectorized execute.

        Works with standard position/fixed-price market order entries,
        but not with conditional trades like stops or limit orders.
    """

    # find trade end points
    long_exit_points = (positions <= 0) & (positions > 0).shift()
    short_exit_points = (positions >= 0) & (positions < 0).shift()

    crosspoint = long_exit_points | short_exit_points
    crosspoint[0] = True
    crosspoint[1] = True

    # efficient way to calculate equity curve
    strategy_returns = (trade_price.pct_change() * positions.shift())

    trade_returns = (strategy_returns + 1).cumprod()[crosspoint].pct_change().dropna()

    result = pandas.DataFrame()
    result['returns'] = strategy_returns.fillna(value=0)
    result['positions'] = positions
    result['trade_returns'] = trade_returns
    result['long_trade_returns'] = trade_returns[long_exit_points]
    result['short_trade_returns'] = trade_returns[short_exit_points]
    return result


def vectorized_execute(data, signals, symbol=None):
    """ Fast vectorized execute.

        Works with standard position/fixed-price market order entries,
        but not with conditional trades like stops or limit orders.
    """
    positions = signals_to_positions(signals)
    result = None
    if isinstance(positions, pandas.Series):
        result = vectorized_execute_one(data[format_field(symbol, t_trade_price, None)], positions)
    elif isinstance(positions, pandas.DataFrame):
        result = pandas.Panel(
            {symbol: vectorized_execute_one(data[format_field(t_trade_price, None)], positions[symbol]) for symbol in positions.columns}
        )
    return positions, result
