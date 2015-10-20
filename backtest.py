import pandas

from pybacktest.execute_fast import vectorized_execute
from pybacktest.execute_iterative import iterative_execute, conditional_signals


class BacktestError(Exception):
    pass


class Backtest(object):
    """

    Attributes
    ----------
    - :positions: pandas.Series
        Strategy positions.

        None if conditional execution (with stop losses or take profits) is used. Position reporting does not make
        sense when stops/takes are present, since they could be closed between timestamps in data.

    """

    def __init__(self, data, strategy, name=None, iterative=False, **kwargs):
        self.name = name
        self.kwargs = kwargs
        self.data = data
        self._verify_data()
        self.strategy = strategy
        self.signals = None
        self._run_strategy()

        self.result = None
        self.positions = None
        self.iterative = iterative or conditional_signals(self.signals)
        if not self.iterative:
            self.positions, self.result = vectorized_execute(self.data, self.signals)
        else:
            self.result = iterative_execute(self.data, self.signals)

    def _verify_data(self):
        if not isinstance(self.data, pandas.DataFrame):
            raise BacktestError('incorrect *data* specification - pandas dataframe is required')

    def _run_strategy(self):
        if callable(self.strategy):
            self.signals = self.strategy(self.data, **self.kwargs)
        elif isinstance(self.strategy, pandas.DataFrame):
            self.signals = self.strategy
        elif isinstance(self.strategy, dict):
            self.signals = pandas.DataFrame(self.strategy)
        else:
            raise BacktestError('*strategy* is not callable or dict or pandas dataframe')

    @property
    def equity(self):
        return (self.result.returns + 1).cumprod()
