import numpy
from backtest.strategies import PositionalStrategy


class MACrossoverStrategy(PositionalStrategy):
    ma_slow = []
    ma_fast = []
    closes = []

    def __init__(self, fast_period=10, slow_period=30, *args, **kwargs):
        super(MACrossoverStrategy, self).__init__(*args, **kwargs)
        self.slow_period = slow_period
        self.fast_period = fast_period

    @property
    def ma_cross(self):
        if len(self.ma_slow) >= 2 and len(self.ma_fast) >= 2:
            if self.ma_fast[-1] > self.ma_slow[-1] and self.ma_fast[-2] < self.ma_slow[-2]:
                return 1
            elif self.ma_fast[-1] < self.ma_slow[-1] and self.ma_fast[-2] > self.ma_slow[-2]:
                return -1
        return 0

    def step(self, bar):
        self.closes.append(bar.C)
        if len(self.closes) < self.slow_period:
            return
        self.ma_slow.append(numpy.mean(self.closes[-self.slow_period:]))
        self.ma_fast.append(numpy.mean(self.closes[-self.fast_period:]))
        if self.position == 0:
            if self.ma_cross > 0:
                self.long()
            elif self.ma_cross < 0:
                self.short()
        else:
            if self.position > 0 and self.ma_cross < 0 or self.position < 0 and self.ma_cross > 0:
                self.exit()
