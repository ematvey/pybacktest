import logging
import itertools
import matplotlib.pyplot as plt


def fxrange(start, end=None, inc=None):
    ''' The xrange function for float '''
    assert inc != 0, "inc should not be zero"
    if end == None:
        end = start
        start = 0.0
    if inc == None:
        inc = 1.0
    i = 0  # to prevent error accumulation
    while True:
        nextv = start + i * inc
        if (inc > 0 and nextv >= end
         or inc < 0 and nextv <= end):
            break
        yield nextv
        i += 1


class Optimizer(object):
    ''' Base optimizer class. Use `add_opt_param` to add optimization
        parameter. Parameter is assumed to be passed as kwarg into strategy. 
    '''

    def __init__(self, backtester_class, data, strategy_class,
                 strategy_args=tuple(), strategy_kwargs=dict(),
                 log_level=None):
        ''' Supply target Backtester class as `backtester_class`.
            For other arguments' description refer to Backtester docstrings.
            NOTE: `data` could not be generator any more.
        '''
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(log_level or logging.INFO)
        self.backtester_class = backtester_class
        self.data = data
        self.strategy_class = strategy_class
        self.strategy_args = strategy_args
        self.strategy_kwargs = strategy_kwargs
        self.opt_params = {}
        self.opt_results = None

    def add_opt_param(self, name, start, stop, step):
        ''' NOTE: opt params should all be added BEFORE calling `run`. '''
        self.opt_params[name] = list(fxrange(start, stop, step))

    def run(self, stats, curve_type='trades'):
        ''' Run optimization.
        In `stats` you should supply iterable of target statistics, 
        corresponding to functions in performance_statistics.py.
        In `curve_type` you should specify which curve should be used for
        stat calculation - either `trades` or `full`. '''
        self.opt_results = {}
        param_names = self.param_names = self.opt_params.keys()
        self.log.info('Running optimization on params: %s', param_names)
        product = itertools.product(*self.opt_params.values())
        c = 1
        for paramset in product:
            pdict = dict(zip(param_names, paramset))
            self.log.info('Optimization step %s: %s', c, pdict)
            backtester = self.backtester_class(
                self.data, self.strategy_class,
                strategy_args=self.strategy_args,
                strategy_kwargs=self.strategy_kwargs,
                run=False, log_level=logging.WARNING)
            backtester.strategy_kwargs.update(pdict)
            backtester.run()
            if curve_type == 'trades':
                curve = backtester.trades_curve
            elif curve_type == 'full':
                curve = backtester.full_curve
            else:
                raise Exception('Requested unrecognized curve_type')
            results = dict(zip(stats, [curve[stat] for stat in stats]))
            self.log.info('Optimization step %s completed: %s', c, results)
            self.opt_results[paramset] = results
            c += 1

    def plot1d(self, stat=None, param=None, show=True):
        ''' 1-d plot of optimization results. Both `stat` and `param` defaults
            to first item from corresponding place. '''
        if not param:
            param = self.param_names[0]
        if not stat:
            stat = self.opt_results.values()[0].keys()[0]
        assert param in self.param_names, 'No opt results on param'
        i = self.param_names.index(param)
        results = [d[stat] for d in self.opt_results.values()]
        param_values = [p[0] for p in self.opt_results.keys()]
        plt.plot(param_values, results)
        plt.xlabel(param or self.param_names[0])
        plt.ylabel(stat)
        plt.title('1d optimization plot')
        if show:
            plt.show()