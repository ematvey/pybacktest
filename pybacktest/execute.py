from abc import abstractmethod

import numpy
import pandas


class Blotter(object):
    def __init__(self, positions, trade_price, mark_price):
        self.positions = positions
        self.trade_price = trade_price
        self.mark_price = mark_price

        self.trade_equity = (
            self.positions.shift() * self.trade_price.pct_change()
        ).fillna(value=0).ix[self.positions == 0]

        self.continuous_price = self.mark_price.copy()
        self.continuous_price[self.trade_price.index] = self.trade_price
        self.continuous_equity = (self.positions.reindex(self.continuous_price.index).ffill().fillna(
            value=0).shift() * self.continuous_price.pct_change()).fillna(value=0)


class SpecError(ValueError):
    pass


class BaseSignal(object):
    def __init__(self):
        self._condition = None
        self._price = None
        self.entry = None

    @property
    def condition(self):
        if self._condition is None:
            raise SpecError("condition is not set or none")
        return self._condition

    @property
    def price(self):
        if self._price is None:
            raise SpecError("price is not set or none")
        return self._price


class BaseExit(BaseSignal):
    def __init__(self):
        super(BaseExit, self).__init__()

    def set_entry(self, entry):
        self.entry = entry


class Entry(BaseSignal):
    def __init__(self, condition, price, volume):
        super(Entry, self).__init__()
        self._condition = condition
        self._price = price
        self.volume = volume
        self.exits = []

    def add_exits(self, *exits):
        for e in exits:
            if not isinstance(e, BaseSignal):
                raise SpecError('Exit bad type: %s' % type(e))
            if hasattr(e, 'set_entry'):
                e.set_entry(self)
            self.exits.append(e)

    def price_at_entry(self):
        return self.price.ix[self.condition].reindex(self.condition.index).ffill().fillna(value=0)

    def calculate_blotter(self):
        assert self.condition.dtype == bool
        assert self.exits

        positions = pandas.Series(index=self.condition.index, dtype='float')
        price = pandas.Series(index=self.condition.index, dtype='float')

        positions.ix[self.condition] = self.volume
        price[self.condition] = self.price[self.condition]

        for ex in self.exits:
            positions.ix[ex.condition] = 0.0
            price.ix[ex.condition] = ex.price[ex.condition]

        positions.iloc[-1] = 0.0
        positions = positions.dropna()
        positions = positions.ix[positions != positions.shift()]

        if numpy.isnan(price.iloc[-1]):
            price.iloc[-1] = self.price.ix[price.index[-1]]

        price = price.ix[positions.index]

        return Blotter(positions, price, self.price)


class Long(Entry):
    def __init__(self, condition, price, volume=1.0):
        super(Long, self).__init__(condition, price, volume)


class Short(Entry):
    def __init__(self, condition, price, volume=-1.0):
        super(Short, self).__init__(condition, price, volume)


class Exit(BaseExit):
    def __init__(self, condition, price):
        super(Exit, self).__init__()
        self._condition = condition
        self._price = price


class BaseStopLoss(BaseExit):
    def __init__(self, trigger_price=None, instant_execution=False):
        super(BaseStopLoss, self).__init__()
        self.trigger_price = trigger_price
        self.instant_execution = instant_execution
        self.stop_level = None

    def set_entry(self, entry):
        self.entry = entry
        self.set_stop_level()

        trigger_price = self.trigger_price if self.trigger_price is not None else entry.price

        if entry.volume > 0:
            self._price = self.stop_level if self.instant_execution else entry.price
            self._condition = trigger_price < self.stop_level

        elif entry.volume < 0:
            self._price = self.stop_level if self.instant_execution else entry.price
            self._condition = trigger_price > self.stop_level

    @abstractmethod
    def set_stop_level(self):
        raise NotImplementedError()


class PercentStopLoss(BaseStopLoss):
    def __init__(self, percent, trigger_price=None, instant_execution=False):
        super(PercentStopLoss, self).__init__(trigger_price=trigger_price, instant_execution=instant_execution)
        self.percent = percent

    def set_stop_level(self):
        price_at_entry = self.entry.price_at_entry()
        if self.entry.volume > 0:
            self.stop_level = price_at_entry * (1 - self.percent)

        elif self.entry.volume < 0:
            self.stop_level = price_at_entry * (1 + self.percent)
