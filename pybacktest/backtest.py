import pandas

from pybacktest.execute_fast import vectorized_execute


class BacktestError(Exception):
    pass


class Backtest(object):
    """

    Attributes
    ----------
    - :positions: pandas.Series
        Strategy positions.

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
        self.positions, self.result = vectorized_execute(self.data, self.signals)

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
    def returns(self):
        if isinstance(self.result, pandas.DataFrame):
            return self.result['returns']
        elif isinstance(self.result, pandas.Panel):
            return self.result.ix[:, :, 'returns'].T.sum()

    @property
    def trade_returns(self):
        if isinstance(self.result, pandas.DataFrame):
            return self.result['trade_returns']
        elif isinstance(self.result, pandas.Panel):
            return self.result.ix[:, :, 'trade_returns'].T.sum()

    @property
    def equity(self):
        return (self.returns + 1).cumprod()

    @property
    def trade_equity(self):
        return (self.trade_returns + 1).cumprod()