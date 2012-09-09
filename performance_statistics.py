import numpy
import random
from scipy.stats.mstats import mquantiles

full = (
    'average',
    'median',
    'sd',
    'mean_profit',
    'mean_loss',
    'median_profit',
    'median_loss',
    'payoff_ratio',
    'sd_profits',
    'sd_losses',
    'winrate',
    'final_equity',
    'profit_factor',
    'sharpe',
    'sortino',
    'maxdd',
    'maxdd_montecarlo',
    'points'
    )
fast = list(full)
fast.remove('maxdd_montecarlo')


def average(changes):
    return numpy.mean(changes[changes != 0])

def median(changes):
    return numpy.median(changes[changes != 0])

def sd(changes):
    return numpy.std(changes[changes != 0])

def points(changes):
    return sum(changes != 0)

def mean_profit(changes):
    return numpy.mean(changes[changes > 0])

def mean_loss(changes):
    return numpy.mean(changes[changes < 0])

def median_profit(changes):
    return numpy.median(changes[changes > 0])

def median_loss(changes):
    return numpy.median(changes[changes < 0])

def payoff_ratio(changes):
    return mean_profit(changes) / -mean_loss(changes)

def sd_profits(changes):
    return numpy.std(changes[changes > 0])

def sd_losses(changes):
    return numpy.std(changes[changes < 0])

def winrate(changes):
    return float(sum(changes > 0)) / sum(changes != 0)

def final_equity(changes):
    return sum(changes)
profit = final_equity

def profit_factor(changes):
    return float(sum(changes[changes > 0])) / -sum(changes[changes < 0])
pf = profit_factor

def sharpe(changes):
    return average(changes) / sd(changes)
sharpe_ratio = sharpe

def sortino(changes):
    return average(changes) / sd_losses(changes)
sortino_ratio = sortino

def maxdd(changes):
    peak = 0
    maxdd = 0
    for price in numpy.cumsum(changes):
        if price > peak:
            peak = price
        if peak - price > maxdd:
            maxdd = peak - price
    return maxdd
maximum_drawdown = max_drawdown = max_dd = maxdd

def recovery_factor(changes):
    return final_equity(changes) / maxdd(changes)
rf = recovery_factor

def maxdd_montecarlo(changes, runs=5000, length=None, serial_dependence=None, 
  quantiles=(0.75, 0.9, 0.975), return_array=False):
    if not length:
        length = len(changes)
    if not serial_dependence:
        seq = changes
        pick = lambda seq: [random.choice(seq)]
    else:
        # Serial dependance detected? Lets sample windows!
        class serial_sampler(object):
            def __init__(self, seq, size):
                self.seq = seq
                self.size = size
            def __len__(self):
                return len(self.seq) - self.size
            def __getitem__(self, i):
                return self.seq[i - self.size : i + self.size]
        pick = lambda seq: random.choice(seq)
        seq = serial_sampler(changes, serial_dependence)
    maxdds = []
    for i in xrange(runs):
        # sample a maxdd
        new_seq = []
        while len(new_seq) < length:
            new_seq += pick(seq)
        maxdds.append(maxdd(new_seq))
    results = {
        'mean maxdd': numpy.mean(maxdds),
        'sd of maxdds': numpy.std(maxdds),
        'quantiles': dict(zip(quantiles, mquantiles(maxdds, quantiles)))
        }
    if return_array:
        results['array of maxdd samples'] = maxdds
    return results
