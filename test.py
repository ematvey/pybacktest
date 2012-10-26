#!/usr/bin/env python

import datetime
import matplotlib.pyplot as plt
import IPython
import logging
logging.basicConfig()
LOGGING_LEVEL = logging.DEBUG

from backtest.testers import SimpleBacktester
from examples.ma_strategy import MACrossoverStrategy as strategy
from datatypes.processing import read_bars

bars = read_bars('examples/testdata/RIZ1.csv')

bt = SimpleBacktester(bars, strategy, log_level=LOGGING_LEVEL)

try:
    import pprint
    pprint.pprint(bt.trades_curve.statistics())
except:
    bt.trades_curve.statistics()

cc = bt.trades_curve

IPython.embed(banner1='trades equity curve stored in `cc`. `cc.series().plot(); plt.show` to plot equity')
