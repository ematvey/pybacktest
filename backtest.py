import pandas
from abc import abstractmethod

from pybacktest.logic import fast_execute, type1_signals_to_positions, \
    type2_signals_to_positions, dummy_signals_to_positions


def signals_to_positions(signals):
    """ Process signals to get positions using different signal-to-positions processing modes
    """
    if isinstance(signals, pandas.Series):
        # option 1: positions
        return signals
    elif isinstance(signals, (dict, pandas.DataFrame)):
        # option 2: full spec with entries/exists (type 1 signals)
        if 'long_entry' in signals or 'short_entry' in signals:
            return type1_signals_to_positions(signals)
        # option 3: separate long/short positions (type 2 signals)
        elif 'long' in signals or 'short' in signals:
            return type2_signals_to_positions(signals)
    raise BacktestError('signals are in unknown form, cannot select processor')


class BacktestError(Exception):
    pass


class BaseBacktest(object):
    def __init__(self, data, strategy, name=None, **kwargs):
        self.name = name
        self.data = self._process_data(data)
        self.signals = self._process_strategy(strategy, data, **kwargs)
        self.positions = signals_to_positions(self.signals)
        self.result = self._execute(self.data, self.positions)

    @abstractmethod
    def _process_data(self, data):
        raise NotImplementedError()
    @abstractmethod
    def _process_strategy(self, strategy, data, **kwargs):
        raise NotImplementedError()
    @abstractmethod
    def _execute(self, data, positions):
        raise NotImplementedError()

    @property
    def cumulative_equity(self):
        return (self.result.equity + 1).cumprod()


class SingleAssetBacktest(BaseBacktest):
    def _process_data(self, data):
        if isinstance(data, pandas.DataFrame):
            return data
        else:
            raise BacktestError('incorrect *data* specification')
    def _process_strategy(self, strategy, data, **kwargs):
        if callable(strategy):
            return strategy(data, **kwargs)
        if isinstance(strategy, pandas.DataFrame):
            return strategy
        else:
            raise BacktestError('strategy is not [callable] and not dict/panel')
    def _execute(self, data, positions):
        if not isinstance(self.positions, pandas.Series):
            raise BacktestError('[internal] must be Series')
        return fast_execute(self.data['trade_price'], self.positions)


class MultiAssetBacktest(BaseBacktest):
    def _process_data(self, data):
        if isinstance(data, pandas.Panel):
            return data
        elif isinstance(data, dict):
            return pandas.Panel(data)
        elif isinstance(data, pandas.DataFrame):
            raise BacktestError('DataFrame *data* is valid only for single-asset')
        else:
            raise BacktestError('incorrect *data* specification')
    def _process_strategy(self, strategy, data, **kwargs):
        if callable(strategy):
            return strategy(data, **kwargs)
        signals = None
        if isinstance(strategy, dict):
            signals = pandas.Panel(strategy)
        elif isinstance(strategy, pandas.Panel):
            signals = strategy
        elif isinstance(strategy, pandas.DataFrame):
            raise BacktestError('strategy specified as signals DataFrame is not compatible with MultiAssetBacktest')
        else:
            raise BacktestError('strategy is not [callable] and not dict/panel')
        return signals
    def _execute(self, data, positions):
        if not isinstance(positions, pandas.DataFrame):
            raise BacktestError('[internal] positions must be DataFrame')
        result = {}
        for symbol in positions.columns:
            result[symbol] = fast_execute(data.ix[symbol, :, 'trade_price'], positions[symbol])
        result = pandas.Panel(result)
        return result


def select_backtest_cls(data):
    if isinstance(data, pandas.DataFrame):
        return SingleAssetBacktest
    elif isinstance(data, (dict, pandas.Panel)):
        return MultiAssetBacktest
    else:
        raise BacktestError('cannot select backtest class')


def backtest(data, strategy, name=None, **kwargs):
    return select_backtest_cls(data)(data, strategy, name=name, **kwargs)
