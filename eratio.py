import matplotlib.pyplot as plt
import numpy as np
from itertools import chain


class ERatioAnalyzer(object):

    total_entries = 0
    entries = []
    finalized = []
    MAE = {}
    MFE = {}

    def __init__(self, length, slippage=0, bars=True):
        self.length = length
        self.slip = slippage
        self.bars = bars
        for i in range(1, self.length):
            self.MAE[i] = []
            self.MFE[i] = []

    def add_entry(self, price, direction):
        self.total_entries += 1
        self.entries.append(
            {'dir': direction,
             'price': price + self.slip if direction > 0 else price - self.slip,
             'MFE': {0: 0}, 'MAE': {0: 0}, 'datapoints_passed': 1})

    def add_datapoint(self, point):
        for entry in self.entries:
            i = entry['datapoints_passed']
            if i >= self.length:
                self.finalized.append(entry)
                self.entries.remove(entry)
                continue
            if self.bars:
                H = point.H
                L = point.L
            else:
                H = point.C
                L = point.L
            if entry['dir'] > 0:
                entry['MFE'][i] = max(H - entry['price'], entry['MFE'][i-1])
                entry['MAE'][i] = max(entry['price'] - L, entry['MAE'][i-1])
            elif entry['dir'] < 0:
                entry['MFE'][i] = max(entry['price'] - L, entry['MFE'][i-1])
                entry['MAE'][i] = max(H - entry['price'], entry['MAE'][i-1])
            entry['datapoints_passed'] += 1

    def finalize(self):
        for entry in chain(self.finalized, self.entries):
            for i in range(1, self.length):
                if i in entry['MAE'] and i in entry['MFE']:
                    self.MAE[i].append(float(entry['MAE'][i]) / 
                                       float(entry['price']))
                    self.MFE[i].append(float(entry['MFE'][i]) / 
                                       float(entry['price']))
        self.finalized = []
        self.entries = []

    def plot(self, median=False, show=True, extra_text=None):
        MAE = self.MAE
        MFE = self.MFE
        MFE_mean = []
        MFE_median = []
        MAE_mean = []
        MAE_median = []
        ERatio_mean = []
        ERatio_median = []
        times = range(1, self.length)
        for i in times:
            MFE_mean.append(np.mean(MFE[i]))
            MFE_median.append(np.median(MFE[i]))
            MAE_mean.append(np.mean(MAE[i]))
            MAE_median.append(np.median(MAE[i]))
            ERatio_mean.append(MFE_mean[-1] / MAE_mean[-1])
            ERatio_median.append(MFE_median[-1] / MAE_median[-1])
        fig = plt.figure()
        if not extra_text == None:
            fig.suptitle('E-ratio / '+extra_text)
        else:
            fig.suptitle('E-ratio')
        plot = fig.add_subplot(111)
        plot.grid(True)
        plot.plot(times, ERatio_mean, 'b')
        if median:
            plot.plot(times, ERatio_median, 'r:')
        if show:
            plt.show()

    def show(self):
        plt.show()



class EntryTester(object):

    def __init__(self, strategy, bars, length=100, skip_first_bar=True):
        '''
        * `strategy` - EntryStrategy object. EntryStrategy is assumed to have `step` method accepting
            datapoints and abstract `entry_callback` method which it feeds with entries of
            (price, volume) format.
        '''
        self.skip_first_bar = skip_first_bar
        self.strategy = strategy
        self.er = ERatioAnalyzer(length)
        self.strategy.entry_callback = self.er.add_entry
        self.bars = bars
        date = None
        for bs in self.bars:
            for b in bs:
                if date == None:
                    date = b.TS.date()
                self.er.add_datapoint(b)
                self.strategy.step(b)
                if self.skip_first_bar and b.TS.date() != date:
                    date = b.TS.date()
                    continue
            self.er.finalize()
        self.er.plot()
