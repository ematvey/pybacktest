import pandas as pd
import numpy as np

from pybacktest.execute_fast import type1_signals_to_positions, type2_signals_to_positions


def test_type1_signals_to_positions():
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

    pos = type1_signals_to_positions(pd.DataFrame(dict(
        long_entry=long_entry, short_entry=short_entry,
        long_exit=long_exit, short_exit=short_exit,
    )))

    cond = (pos.values == np.array([0, 1, 1, 0, 0, -1, -1, 1, 1, 0])).all()
    assert cond


def test_type2_signals_to_positions():
    long_s = pd.Series(False, index=range(10))
    short_s = long_s.copy()

    long_s.iloc[1:3] = True
    short_s.iloc[5:7] = True

    pos = type2_signals_to_positions(pd.DataFrame(dict(
        long=long_s, short=short_s,
    )))

    cond = (pos.values == np.array([0, 1, 1, 0, 0, -1, -1, 0, 0, 0])).all()
    assert cond
