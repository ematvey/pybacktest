''' Auxilliary classes to group bars into bigger bars '''

from datatypes.datapoint import bar as Bar


class BaseGrouper(object):
    def __init__(self, callback):
        self.cb = callback
    def initbar(self, bar):
        self.b = Bar()
        self.b.timestamp = bar.timestamp
        self.b.O = bar.O
        self.b.H = bar.H
        self.b.L = bar.L
        self.b.C = bar.C
        self.b.V = bar.V
    def step_condition(self, bar):
        raise NotImplementedError
    def __call__(self, bar):
        if not hasattr(self, 'b'):
            self.initbar(bar)
            return
        if self.step_condition(bar):
            res = self.cb(self.b)
            self.initbar(bar)
            return res
        self.b.C = bar.C
        self.b.H = max(self.b.H, bar.H)
        self.b.L = min(self.b.L, bar.L)
        self.b.V += bar.V


class GrouperM15(BaseGrouper):
    def step_condition(self, bar):
        return bar.timestamp.minute % 15 == 0


class GrouperDaily(BaseGrouper):
    def step_condition(self, bar):
        return not self.b.timestamp.date() == bar.timestamp.date()
