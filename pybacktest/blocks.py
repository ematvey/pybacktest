# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

import numbers
from abc import abstractmethod

import numpy
import pandas

__all__ = ['SpecError',
           'Entry', 'Long', 'Short',
           'Exit', 'TimeExit', 'PercentStopLoss', 'PercentTakeProfit']


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
        if not isinstance(value, (pandas.Series, numpy.ndarray)):
            raise SpecError(
                "condition has incorrect type: %s (should be <pandas.Series> or <numpy.ndarray>)" % type(value))
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
        if not isinstance(value, (pandas.Series, numpy.ndarray)):
            raise SpecError(
                "condition has incorrect type: %s (should be <pandas.Series> or <numpy.ndarray>)" % type(self._price))
        self._price = value

    def transaction_price(self, cost_percent=None, cost_points=None):
        """
        Get trade price after transaction costs have been applied.

        :param cost_percent: Tx cost in % of asset value.
            If individual costs are assigned to this signal,
            it will be ignored.
        :param cost_points: Tx cost in points of asset price.
            If individual costs are assigned to this signal,
            it will be ignored.
        :return: Transaction price series.
        """
        if self.transaction_costs_assigned:
            cost_percent = self.txcost_pct
            cost_points = self.txcost_points
        if cost_percent is None:
            cost_percent = 0.0
        if cost_points is None:
            cost_points = 0.0
        if self.volume > 0:
            return (self.price + cost_points) * (1 + cost_percent / 100)
        elif self.volume < 0:
            return (self.price - cost_points) * (1 - cost_percent / 100)
        else:
            raise ValueError('Incorrect Volume amount: %s' % self.volume)

    @property
    def transaction_costs_assigned(self):
        return self.txcost_points is not None or self.txcost_pct is not None

    def __repr__(self):
        return self.__class__.__name__


class BaseExit(BaseSignal):
    def __init__(self, **options):
        super(BaseExit, self).__init__(**options)

    def _set_entry(self, entry):
        self.entry = entry

    @property
    def volume(self):
        return -self.entry.volume


class Entry(BaseSignal):
    """Generic entry signal"""

    def __init__(self, condition, price, volume, **options):
        """
        :param condition: Entry condition.
            pandas.Series with boolean values.
        :param price: Trade price for entries.
            pandas.Series with float values.
        :param volume: Directional volume of entry. Volume ==1 is Long, ==-1 is Short.
            pandas.Series with float values.
        """
        super(Entry, self).__init__(**options)
        self.condition = condition
        self.price = price
        self.volume = volume
        self.exits = []

    def exit(self, *exits):
        """
        Attach Exit to this Entry

        :param exits: List of Exits to attach
        """
        for e in exits:
            if not isinstance(e, BaseSignal):
                raise SpecError('Exit bad type: %s' % type(e))
            if isinstance(e, BaseExit):
                e._set_entry(self)
            self.exits.append(e)
        return self

    def price_at_entry(self):
        return self.price.ix[self.condition].reindex(self.condition.index).ffill().fillna(value=0)


class Long(Entry):
    """Long entry signal"""

    def __init__(self, condition, price, **options):
        """
        :param condition: Long entry condition.
            pandas.Series with boolean values.
        :param price: Trade price for entries.
            pandas.Series with float values.
        """
        super(Long, self).__init__(condition, price, volume=1.0, **options)


class Short(Entry):
    """Short entry signal"""

    def __init__(self, condition, price, **options):
        """
        :param condition: Short entry condition.
            pandas.Series with boolean values.
        :param price: Trade price for entries.
            pandas.Series with float values.
        """
        super(Short, self).__init__(condition, price, volume=-1.0, **options)


class Exit(BaseExit):
    """Generic exit signal"""

    def __init__(self, condition, price=None, **options):
        """
        :param condition: Exit condition.
            pandas.Series with boolean values.
        :param price: Price of exits (defaults to Entry price).
            pandas.Series with float values.
        """
        super(Exit, self).__init__(**options)
        self.condition = condition
        self.price = price

    def _set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self.price = self.entry.price


class TimeExit(BaseExit):
    """Exit after given number of periods (time steps, as infered from data)"""

    def __init__(self, periods, price=None, **options):
        super(TimeExit, self).__init__(**options)
        self.periods = periods
        self.price = price

    def _set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self.price = self.entry.price
        self.condition = self.entry.condition.shift(self.periods).fillna(value=False)


class BaseConditionalExit(BaseExit):
    def __init__(self, trigger_price=None, instant_execution=False, **options):
        super(BaseConditionalExit, self).__init__(**options)
        self.trigger_price = trigger_price
        self.instant_execution = instant_execution
        self.stop_level = None
        self.stop_active = None

    def _set_entry(self, entry):
        self.entry = entry
        self._set_level()
        if self.trigger_price is None:
            self.trigger_price = self.entry.price
        self.price = self.stop_level if self.instant_execution else entry.price
        self.stop_active = (self.trigger_price != 0) & (self.stop_level != 0)
        self.condition = self._get_condition() & self.stop_active

    @abstractmethod
    def _set_level(self):
        raise NotImplementedError()

    @abstractmethod
    def _get_condition(self):
        raise NotImplementedError()


class BaseStopLoss(BaseConditionalExit):
    def _get_condition(self):
        if self.entry.volume > 0:
            return self.trigger_price < self.stop_level
        elif self.entry.volume < 0:
            return self.trigger_price > self.stop_level


class BaseTakeProfit(BaseConditionalExit):
    def _get_condition(self):
        if self.entry.volume > 0:
            return self.trigger_price > self.stop_level
        elif self.entry.volume < 0:
            return self.trigger_price < self.stop_level


class PercentStopLoss(BaseStopLoss):
    """Stop Loss exit, defined in terms of percent of asset price"""

    def __init__(self, percent, trigger_price=None, instant_execution=False):
        super(PercentStopLoss, self).__init__(trigger_price=trigger_price, instant_execution=instant_execution)
        self.percent = percent

    def _set_level(self):
        price_at_entry = self.entry.price_at_entry()
        if self.entry.volume > 0:
            self.stop_level = price_at_entry * (1 - self.percent)

        elif self.entry.volume < 0:
            self.stop_level = price_at_entry * (1 + self.percent)


class PercentTakeProfit(BaseTakeProfit):
    """Take Profit exit, defined in terms of percent of asset price"""

    def __init__(self, percent, trigger_price=None, instant_execution=False):
        super(PercentTakeProfit, self).__init__(trigger_price=trigger_price, instant_execution=instant_execution)
        self.percent = percent

    def _set_level(self):
        price_at_entry = self.entry.price_at_entry()
        if self.entry.volume > 0:
            self.stop_level = price_at_entry * (1 + self.percent)

        elif self.entry.volume < 0:
            self.stop_level = price_at_entry * (1 - self.percent)
