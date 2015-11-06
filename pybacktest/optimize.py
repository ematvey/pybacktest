from itertools import product

import pandas as pd

from pybacktest.backtest import Backtest


def parameter_grid(param_grid):
    keys = []
    vals = []
    for key, val in param_grid.items():
        keys.append(key)
        vals.append(val)
    for par in product(*vals):
        yield dict(zip(keys, par))


def bruteforce(data, strategy_fn, opt_params, evaluation_func, verbose=False):
    score = 0
    params = {}
    grid = list(parameter_grid(opt_params))
    if verbose: print('bruteforce: grid size %s' % len(grid))
    for par in grid:
        bt = Backtest(data, lambda d: strategy_fn(d, **par))
        s = evaluation_func(bt.result.equity)
        if s > score:
            score = s
            params = par
    return params


def ret_to_mdd(eq):
    c = (eq + 1).cumprod()
    mdd = (pd.expanding_max(c) - c).max()
    return c.sum() / mdd


def final_equity(eq):
    return (eq + 1).prod()


class WalkForwardTest(object):
    def __init__(
            self, data, strategy, opt_params,
            optimize_window_size=90, test_window_size=60,
            evaluation_func=final_equity,
            optimization_func=bruteforce,
            verbose=True,
    ):
        assert callable(strategy)
        need_opt_verbosity = False
        if verbose:
            need_opt_verbosity = True

        self.backtests = []
        _opt = []
        i = optimize_window_size
        l = len(data)
        while i < l:
            opt_sample = data.iloc[i - optimize_window_size:i]
            test_sample = data.iloc[i:i + test_window_size]

            params = optimization_func(opt_sample, strategy, opt_params, evaluation_func, verbose=need_opt_verbosity)
            need_opt_verbosity = False

            _o = {'date': data.index[i]}
            _o.update(params)
            _opt.append(_o)

            assert isinstance(params, dict)
            self.backtests.append(Backtest(test_sample, lambda d: strategy(d, **params)))

            if verbose:
                print(
                    'walk-forward %4.1f%s done [%s]' % (
                        100 * (i - test_window_size) / (l - test_window_size), '%', data.index[i]
                    ))

            i += test_window_size

        self.optimal_params = pd.DataFrame(_opt).set_index('date', drop=True)

        result = []
        for i, bt in enumerate(self.backtests):
            r = bt.result.copy()
            result.append(r)
        self.result = pd.concat(result, axis=0)
