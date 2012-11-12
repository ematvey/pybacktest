#!/usr/bin/env python

try:
    import pyaux
    pyaux.use_exc_ipdb()
    pyaux.use_exc_log()
except:
    pass

import datetime
import matplotlib.pyplot as plt
import IPython
import logging

logging.basicConfig()

from backtest.testers import SimpleBacktester
from examples.ma_strategy import MACrossoverStrategy as strategy
from datatypes.pandas_bars import pandas_bars_wrap
from datatypes.quotes import get_daily_quotes_yahoo

bars = pandas_bars_wrap(get_daily_quotes_yahoo('GOLD', '20070101', '20120101'))
bars = [list(bars)]

#IPython.embed()

bt = SimpleBacktester(bars, strategy,
                      strategy_kwargs={'fast_period': 10, 'slow_period': 25},
                      log_level=logging.DEBUG)

try:
    import pprint
    pprint.pprint(bt.trades_curve.statistics())
except:
    print bt.trades_curve.statistics()

cc = bt.trades_curve

IPython.embed(banner1='trades equity curve stored in `cc`. `cc.series().plot(); plt.show()` to plot equity')
