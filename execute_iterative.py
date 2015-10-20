import pandas

from pybacktest.execute_defs import *


def conditional_signals(signals):
    for f in conditional_column_tokens:
        for column in signals:
            if column.endswith(f):
                return True
    return False


def iterative_execute_one(data, signals):
    raise NotImplementedError('strategy requires iterative execution which is not implented yet')


def iterative_execute(data, signals):
    signals, multi = parse_signals_dataframe(signals, all_tokens)
    if len(signals) == 1:
        return iterative_execute_one(data, signals[list(signals.keys())[0]])
    else:
        return pandas.Panel({symbol: iterative_execute_one(data, s) for symbol, s in signals.items()})
