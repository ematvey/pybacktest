import pandas as pd
import numpy as np

from pybacktest.backtest import process_signals


def test_process_signals():
    long_entry = pd.Series(False, index=range(10))
    long_exit = long_entry.copy()
    short_entry = long_entry.copy()
    short_exit = long_entry.copy()

    long_entry[1] = True
    long_exit[3] = True
    short_entry[5] = True
    long_entry[7] = True
    short_exit[8] = True
    long_exit[9] = True

    pos = process_signals(long_entry, short_entry, long_exit, short_exit)

    cond = (pos.values == np.array([0, 1, 1, 0, 0, -1, -1, 1, 1, 0])).all()
    assert cond
