# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Production-related code, used to extract signals from Backtest. """


from pybacktest.backtest import Backtest


def check_position_change(strategy_outs):
    """ Runs a backtest and returns position if it changed on last bar
    (and needs execution) or None if it did not.

    `strategy_outs` - frame returned by strategy function.

    NOTE: both 0 position and None are converted to False, so you should
    use `if position is None: execute`, not `if position: execute`, or you
    will never close your position. """

    bt = Backtest(strategy_outs)
    pos = bt.positions.reindex(bt.ohlc.index).ffill().fillna(value=0)

    if pos.iloc[-1] != pos.iloc[-2]:
        return pos.iloc[-1]
