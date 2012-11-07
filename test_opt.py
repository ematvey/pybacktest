#!/usr/bin/env python

import datetime
import matplotlib.pyplot as plt
import IPython
import logging

logging.basicConfig()
LOGGING_LEVEL = logging.DEBUG

from backtest.testers import SimpleBacktester
from backtest.opt import Optimizer
from examples.ma_strategy import MACrossoverStrategy as strategy
from datatypes.processing import read_bars

bars = read_bars('examples/testdata/RIZ1.csv')

opt = Optimizer(SimpleBacktester, bars, strategy, log_level=LOGGING_LEVEL)
opt.add_opt_param('fast_period', 5, 20, 5)
opt.run(('sharpe',))

print 'Param names: %s' % opt.param_names
print 'Optimization results (param vector : resulting statistics)'
try:
    import pprint
    pprint.pprint(opt.opt_results)
except:
    print opt.opt_results


IPython.embed(banner1='optimizer is in `opt`')
