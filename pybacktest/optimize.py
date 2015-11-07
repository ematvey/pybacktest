from itertools import product

import pandas as pd

from pybacktest.backtest import Backtest


def paramgrid(param_grid):
    keys = []
    vals = []
    for key, val in param_grid.items():
        keys.append(key)
        vals.append(val)
    for par in product(*vals):
        yield dict(zip(keys, par))


def bruteforce(data, strategy_fn, opt_params, evaluation_func, verbose=False):
    score = 0
    params = None
    grid = list(paramgrid(opt_params))
    if verbose:
        print('bruteforce: grid size %s' % len(grid))
    for par in grid:
        bt = Backtest(strategy_fn(data, **par))
        s = evaluation_func(bt.performance.trade_equity)
        if s > score:
            score = s
            params = par
    return params


def final_equity(eq):
    return eq.iloc[-1]


class WalkForwardTest(object):
    def __init__(
            self, data, strategy, opt_params,
            backtest_options=None,
            strategy_options=None,
            optimize_window=90, test_window=60,
            evaluation_func=final_equity,
            optimization_func=bruteforce,
            verbose=True,
    ):
        assert callable(strategy)
        assert isinstance(opt_params, dict)

        need_opt_verbosity = False
        if verbose:
            need_opt_verbosity = True

        _opt = []
        i = optimize_window
        l = len(data)

        self.in_sample_optimized = pd.DataFrame(columns=opt_params.keys())

        while i < l:
            in_sample = data.iloc[i - optimize_window:i]
            out_of_sample = data.iloc[i:i + test_window]

            params = optimization_func(in_sample, strategy, opt_params, evaluation_func, verbose=need_opt_verbosity)
            need_opt_verbosity = False

            _o = {'date': data.index[i]}
            _o.update(params)
            _opt.append(_o)

            assert isinstance(params, dict)

            if verbose:
                print(
                    'walk-forward %4.1f%s done [%s]' % (
                        100 * (i - test_window) / (l - test_window), '%', data.index[i]
                    ))

            i += test_window

        self.optimal_params = pd.DataFrame(_opt).set_index('date', drop=True)
