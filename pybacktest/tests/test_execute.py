from numpy import array
import pandas as pd

from pybacktest.execute import Long, PercentStopLoss, Exit, Short


def test_simple_1():
    en = pd.Series([0, 0, 1, 0, 0, 1, 0, 1, 0, 0], dtype='bool')
    ex = pd.Series([0, 0, 0, 0, 1, 0, 0, 0, 0, 0], dtype='bool')
    price = pd.Series([1, 2, 4, 5, 8, 4, 5, 8, 4, 1], dtype='float')

    entry = Long(en, price)
    entry.add_exits(Exit(ex, price))

    p = entry.calculate_blotter()

    assert (p.continuous_equity.values.round(5) == array([0., 0., 0., 0.25, 0.6, 0., 0.25, 0.6, -0.5, -0.75])).all()
    assert (p.trade_equity.values.round(5) == array([1., -0.75])).all()


def test_simple_2():
    le = pd.Series([0, 1, 0, 0, 0, 0, 0], dtype='bool')
    se = pd.Series([0, 0, 0, 1, 0, 0, 0], dtype='bool')
    sx = pd.Series([0, 0, 0, 0, 0, 1, 0], dtype='bool')
    pr = pd.Series([1, 2, 4, 8, 6, 3, 2], dtype='float')

    lentry = Long(le, pr)
    sentry = Short(se, pr)

    sentry.add_exits(Exit(sx, pr))

    lentry.add_exits(sentry)

    p1 = lentry.calculate_blotter()

    p2 = sentry.calculate_blotter()

    assert (p1.continuous_equity.values == array([0., 0., 1., 1., -0., -0., -0.])).all()

    assert (p2.continuous_equity.values == array([0., 0., 0., 0., 0.25, 0.5, -0.])).all()


def test_pct_stoploss():
    en1 = pd.Series([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], dtype='bool')
    pr1 = pd.Series([1, 2, 4, 5, 8, 4, 5, 8, 4, 1], dtype='float')

    en1 = Long(en1, pr1)
    en1.add_exits(
        PercentStopLoss(0.1,
                        instant_execution=True),
    )

    p = en1.calculate_blotter()

    assert (p.trade_equity.values.round(5) == array([-0.1])).all()
    assert (p.continuous_equity.values.round(5) == array([0., 0., 1., 0.25, 0.6, -0.5, 0.25, 0.6, -0.5, -0.55])).all()
