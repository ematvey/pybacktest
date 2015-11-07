from abc import abstractmethod

__all__ = ['SpecError', 'Entry', 'Long', 'Short', 'Exit', 'TimeExit', 'PercentStopLoss']


class SpecError(ValueError):
    pass


class BaseSignal(object):
    def __init__(self, txcost_pct=0.0, txcost_points=0.0):
        self._condition = None
        self._price = None
        self._volume = 0.0
        self.entry = None
        self.txcost_pct = txcost_pct
        self.txcost_points = txcost_points

    @property
    def volume(self):
        return self._volume

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

    @property
    def transaction_price(self):
        if self.volume > 0:
            return (self.price + self.txcost_points) * (1 + self.txcost_pct / 100)
        elif self.volume < 0:
            return (self.price - self.txcost_points) * (1 - self.txcost_pct / 100)
        else:
            raise ValueError('[critical] Volume is not set')


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
        self._condition = condition
        self._price = price
        self._volume = volume
        self.exits = []

    def add_exits(self, *exits):
        for e in exits:
            if not isinstance(e, BaseSignal):
                raise SpecError('Exit bad type: %s' % type(e))
            if isinstance(e, BaseExit):
                e.set_entry(self)
            self.exits.append(e)

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
        self._condition = condition
        self._price = price

    def set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self._price = self.entry.price


class TimeExit(BaseExit):
    def __init__(self, periods, price=None, **options):
        super(TimeExit, self).__init__(**options)
        self.periods = periods
        self._price = price

    def set_entry(self, entry):
        self.entry = entry
        if self._price is None:
            self._price = self.entry.price
        self._condition = self.entry.condition.shift(self.periods).fillna(value=False)


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
            self._price = self.stop_level if self.instant_execution else entry.price
            self._condition = (trigger_price < self.stop_level) & stop_cond

        elif entry.volume < 0:
            self._price = self.stop_level if self.instant_execution else entry.price
            self._condition = (trigger_price > self.stop_level) & stop_cond

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
