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
from backtest.opt import Optimizer
from examples.ma_strategy import MACrossoverStrategy as strategy
from datatypes.pandas_bars import pandas_bars_wrap
from datatypes.quotes import get_daily_quotes_yahoo

bars = pandas_bars_wrap(get_daily_quotes_yahoo('GOLD', '20070101', '20120101'))
bars = [list(bars)]

opt = Optimizer(SimpleBacktester, bars, strategy, log_level=logging.DEBUG)
opt.add_opt_param('fast_period', 5, 20, 5)
opt.add_opt_param('slow_period', 20, 50, 5)
opt.run(('sharpe',))

print 'Param names: %s' % opt.param_names
print 'Optimization results (param vector : resulting statistics)'
try:
    import pprint
    pprint.pprint(opt.opt_results)
except:
    print opt.opt_results


IPython.embed(banner1='optimizer is in `opt`')
