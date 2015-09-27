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


def bruteforce(backtest_cls, strategy_fn, data, opt_params, evaluation_func):
    score = 0
    params = {}
    grid = list(parameter_grid(opt_params))
    print('bruteforce: grid size %s' % len(grid))
    for par in grid:
        bt = backtest_cls(data, lambda d: strategy_fn(d, **par))
        s = evaluation_func(bt.result.equity)
        if s > score:
            score = s
            params = par
    return params


def equity_eval_func(eq):
    return (eq + 1).prod()


class WalkForwardTest(object):
    def __init__(
            self, data, strategy, opt_params,
            optimize_window_size=90, test_window_size=60,
            evaluation_func=equity_eval_func,
            optimization_func=bruteforce,
            backtest_cls=Backtest,
            verbose=True,
    ):
        assert callable(strategy)

        self.backtests = []

        _opt = []

        i = optimize_window_size
        l = len(data)
        while i < l:
            opt_sample = data.iloc[i - optimize_window_size:i]
            test_sample = data.iloc[i:i + test_window_size]
            params = optimization_func(backtest_cls, strategy, opt_sample, opt_params, evaluation_func)

            _o = {'date': data.index[i]}
            _o.update(params)
            _opt.append(_o)

            assert isinstance(params, dict)
            self.backtests.append(backtest_cls(test_sample, lambda d: strategy(d, **params)))

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
            r['i'] = i
            result.append(r)
        self.result = pd.concat(result, axis=0)
