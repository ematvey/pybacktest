import numbers
from abc import abstractmethod

import pandas

__all__ = ['SpecError', 'Entry', 'Long', 'Short', 'Exit', 'TimeExit', 'PercentStopLoss']


class SpecError(ValueError):
    pass


class BaseSignal(object):
    def __init__(self, txcost_pct=None, txcost_points=None, **options):
        if len(options) > 0:
            raise SpecError('Unhandled Options passed: %s' % (list(options.keys()),))
        self._condition = None
        self._condition_set = False
        self._price = None
        self._price_set = False
        self._volume = None
        self._volume_set = False
        self.entry = None
        self.txcost_pct = txcost_pct
        self.txcost_points = txcost_points

    @property
    def volume(self):
        if self._volume is None:
            raise SpecError("volume is not set")
        return self._volume

    @volume.setter
    def volume(self, value):
        if value is None:
            return
        if not isinstance(value, numbers.Number):
            raise SpecError("volume has incorrect type: %s (should be number)" % type(value))
        self._volume = value

    @property
    def condition(self):
        if self._condition is None:
            raise SpecError("condition is not set")
        return self._condition

    @condition.setter
    def condition(self, value):
        if value is None:
            return
        if not isinstance(value, pandas.Series):
            raise SpecError("condition has incorrect type: %s (should be <pandas.Series>)" % type(value))
        self._condition = value

    @property
    def price(self):
        if self._price is None:
            raise SpecError("price is not set")
        return self._price

    @price.setter
    def price(self, value):
        if value is None:
            return
        if not isinstance(value, pandas.Series):
            raise SpecError("condition has incorrect type: %s (should be <pandas.Series>)" % type(self._price))
        self._price = value

    def get_transaction_price(self, cost_percent, cost_points):
        if cost_percent is None:
            cost_percent = 0.0
        if cost_points is None:
            cost_points = 0.0
        if self.volume > 0:
            return (self.price + cost_points) * (1 + cost_percent / 100)
        elif self.volume < 0:
            return (self.price - cost_points) * (1 - cost_percent / 100)
        else:
            raise ValueError('[critical] Volume is not set')

    @property
    def transaction_price(self):
        return self.get_transaction_price(self.txcost_pct, self.txcost_points)

    @property
    def transaction_costs_assigned(self):
        return self.txcost_points is not None or self.txcost_pct is not None


class BaseExit(BaseSignal):
    def __init__(self, **options):
        super(BaseExit, self).__init__(**options)

    def set_entry(self, entry):
        self.entry = entry

    @property
    def volume(self):
        return -self.entry.volume


class Entry(BaseSignal):
    def __init__(self, condition, price, volume, **options):
        super(Entry, self).__init__(**options)
        self.condition = condition
        self.price = price
        self.volume = volume
        self.exits = []

    def exit(self, *exits):
        for e in exits:
            if not isinstance(e, BaseSignal):
                raise SpecError('Exit bad type: %s' % type(e))
            if isinstance(e, BaseExit):
                e.set_entry(self)
            self.exits.append(e)
        return self

    def price_at_entry(self):
        return self.price.ix[self.condition].reindex(self.condition.index).ffill().fillna(value=0)


class Long(Entry):
    def __init__(self, condition, price, volume=1.0, **options):
        super(Long, self).__init__(condition, price, volume, **options)


class Short(Entry):
    def __init__(self, condition, price, volume=-1.0, **options):
        super(Short, self).__init__(condition, price, volume, **options)


class Exit(BaseExit):
    def __init__(self, condition, price=None, **options):
        super(Exit, self).__init__(**options)
        self.condition = condition
        self.price = price

    def set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self.price = self.entry.price


class TimeExit(BaseExit):
    def __init__(self, periods, price=None, **options):
        super(TimeExit, self).__init__(**options)
        self.periods = periods
        self.price = price

    def set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self.price = self.entry.price
        self.condition = self.entry.condition.shift(self.periods).fillna(value=False)


class BaseStopLoss(BaseExit):
    def __init__(self, trigger_price=None, instant_execution=False, **options):
        super(BaseStopLoss, self).__init__(**options)
        self.trigger_price = trigger_price
        self.instant_execution = instant_execution
        self.stop_level = None

    def set_entry(self, entry):
        self.entry = entry
        self.set_stop_level()

        trigger_price = self.trigger_price if self.trigger_price is not None else entry.price

        stop_cond = (trigger_price != 0) & (self.stop_level != 0)

        if entry.volume > 0:
            self.price = self.stop_level if self.instant_execution else entry.price
            self.condition = (trigger_price < self.stop_level) & stop_cond

        elif entry.volume < 0:
            self.price = self.stop_level if self.instant_execution else entry.price
            self.condition = (trigger_price > self.stop_level) & stop_cond

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
