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

logging.basicConfig(log_level=logging.DEBUG)

from backtest.testers import SimpleBacktester
from backtest.opt import Optimizer
from examples.ma_strategy import MACrossoverStrategy as strategy
from datatypes.processing import read_bars

bars = read_bars('examples/testdata/RIZ1.csv')

opt = Optimizer(SimpleBacktester, bars, strategy)
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
