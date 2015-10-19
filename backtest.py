import pandas

from pybacktest.logic import fast_execute, signals_to_positions


class BacktestError(Exception):
    pass


class Backtest(object):
    def __init__(self, data, strategy, name=None, **kwargs):
        self.name = name
        self.data = self._process_data(data)
        self.signals = self._process_strategy(strategy, data, **kwargs)
        self.positions = self._process_signals(self.signals)
        self.result = self._execute_positions(self.data, self.positions)

    @staticmethod
    def _process_data(data):
        if isinstance(data, pandas.DataFrame):
            return data
        else:
            raise BacktestError('incorrect *data* specification')

    @staticmethod
    def _process_strategy(strategy, data, **kwargs):
        if callable(strategy):
            return strategy(data, **kwargs)
        elif isinstance(strategy, pandas.DataFrame):
            return strategy
        elif isinstance(strategy, dict):
            return pandas.DataFrame(strategy)
        else:
            raise BacktestError('*strategy* is not callable or dict or pandas dataframe')

    @staticmethod
    def _process_signals(signals):
        return signals_to_positions(signals)

    @staticmethod
    def _execute_positions(data, positions):
        if isinstance(positions, pandas.Series):
            return fast_execute(data['trade_price'], positions)
        elif isinstance(positions, pandas.DataFrame):
            return pandas.Panel(
                {instrument: fast_execute(data['%s_trade_price' % instrument], positions[instrument])
                 for instrument in positions.columns}
            )

    @property
    def equity(self):
        return (self.result.returns + 1).cumprod()
