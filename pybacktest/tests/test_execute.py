import pandas as pd
from numpy import array

from pybacktest.blocks import Long, PercentStopLoss, Exit, Short, TimeExit
from pybacktest.blotter import Blotter


def test_simple_1():
    en = pd.Series([0, 0, 1, 0, 0, 1, 0, 1, 0, 0], dtype='bool')
    ex = pd.Series([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype='bool')
    price = pd.Series([1, 2, 4, 5, 8, 4, 5, 8, 4, 1], dtype='float')

    entry = Long(en, price)
    entry.add_exits(Exit(ex, price))

    p = Blotter(entry)

    assert (p.continuous_returns.values.round(5) == array([0., 0., 0., 0.25, 0.6, 0., 0.25, 0.6, -0.5, -0.75])).all()
    assert (p.trade_returns.values.round(5) == array([0, 1, 0, -0.75])).all()


def test_simple_2():
    le = pd.Series([0, 1, 0, 0, 0, 0, 0], dtype='bool')
    se = pd.Series([0, 0, 0, 1, 0, 0, 0], dtype='bool')
    sx = pd.Series([0, 0, 0, 0, 0, 1, 0], dtype='bool')
    pr = pd.Series([1, 2, 4, 8, 6, 3, 2], dtype='float')

    lentry = Long(le, pr)
    sentry = Short(se, pr)

    sentry.add_exits(Exit(sx, pr))
    lentry.add_exits(sentry)

    p1 = Blotter(lentry)
    p2 = Blotter(sentry)

    assert (p1.continuous_returns.values == array([0., 0., 1., 1., -0., -0., -0.])).all()

    assert (p2.continuous_returns.values == array([0., 0., 0., 0., 0.25, 0.5, -0.])).all()


def test_time_exit():
    sig = pd.Series([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype='bool')
    pr1 = pd.Series([1, 2, 4, 5, 8, 4, 5, 8, 4, 1], dtype='float')
    en1 = Long(sig, pr1)
    te = TimeExit(3)
    en1.add_exits(te)
    assert (te.condition == sig.shift(3).fillna(value=0)).all()
    assert (te.price == en1.price).all()


def test_pct_stoploss():
    sig = pd.Series([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype='bool')
    pr1 = pd.Series([1, 2, 4, 5, 8, 4, 5, 8, 4, 1], dtype='float')

    en1 = Long(sig, pr1)
    en1.add_exits(
        PercentStopLoss(0.1, instant_execution=True),
    )
    p1 = Blotter(en1)
    assert (p1.trade_returns.values.round(5) == array([0, -0.1])).all()
    assert (p1.continuous_returns.values.round(5) == array([0., 0., 1., 0.25, 0.6, -0.5, 0.25, 0.6, -0.5, -0.55])).all()

    en2 = Short(sig, pr1)
    en2.add_exits(
        PercentStopLoss(0.1, instant_execution=True),
    )
    p2 = Blotter(en2)
    assert (p2.trade_returns.values.round(5) == array([0, -0.1])).all()
    assert (p2.continuous_returns.values.round(5) == array([0, 0, -0.1, 0, 0, 0, 0, 0, 0, 0])).all()
