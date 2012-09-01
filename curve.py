import numpy as np
from scipy.stats.mstats import mquantiles
import matplotlib.pyplot as plt
import datetime
import random
import pandas
from math import log

def merge_curves(curves):
    r = EquityCurve()
    for c in curves:
        r = c.merge(r)
    return r

class EquityCurve(object):
    """ Increment-based Equity Curve with automatic calculation of various statistics. """

    def __init__(self):
        self._seq = [] # base sequence (timestamp, diff); DO NOT CHANGE EXTERNALLY
        self._cumsum = 0 # current cumsum; DO NOT CHANGE EXTERNALLY
        self._cumsum_seq = [] # derived cumsum sequence; DO NOT CHANGE EXTERNALLY

    def __repr__(self):
        i = self._seq
        if len(i)>0:
            s = self.statistics()
            return '<EquityCurve {start}..{stop} len={Points} mean={Average} sd={SD}>'.format(
              start=i[0][0].date(), stop=i[-1][0].date(), **s)
        else:
            return '<empty EquityCurve>'

    def _get_cumsum_seq(self):
        """ calc cumsum sequence, analogous to _seq """
        if len(self._cumsum_seq) == len(self._seq):
            return self._cumsum_seq
        curve = []
        cumsum = 0
        for i in self._seq:
            cumsum += i[1]
            curve.append((i[0], cumsum))
        self._cumsum_seq = curve
        return curve

    @property
    def increments(self):
        """ TimeSeries of Equity diffs over time """
        return pandas.TimeSeries(data=[i[1] for i in self._seq], index=[i[0] for i in self._seq])
    diffs = changes = increments

    @property
    def curve(self):
        """ TimeSeries of Equity values over time """
        curve = self._get_cumsum_seq()
        return pandas.TimeSeries(data=[i[1] for i in curve], index=[i[0] for i in curve])

    @property
    def length(self):
        return len(self._seq)

    def add_point(self, timestamp, equity):
        """ Add new equity point to the curve """
        self._seq.append((timestamp, equity-self._cumsum))
        self._cumsum = equity
    def add_change(self, timestamp, diff):
        """ Add new change point to the curve """
        self._seq.append((timestamp, diff))
        self._cumsum += diff

    def merge(self, curve):
        """ Merge given curve into this curve """
        # XXX should be based off time series addition? or w/e?
        c1 = self._seq
        if len(c1)==0:
            return curve
        c2 = curve.increments
        if len(c2)==0:
            return self
        r = EquityCurve()
        i = 0; j = 0
        while i<len(c1) or j<len(c2):
            if i<len(c1) and j<len(c2) and c1[i][0] == c2[j][0]:
                r.increments.append((c1[i][0], c1[i][1]+c2[j][1]))
                i += 1
                j += 1
            elif j>=len(c2) or i<len(c1) and c1[i][0] < c2[j][0]:
                r.increments.append((c1[i][0], c1[i][1]))
                i += 1
            elif i>=len(c1) or j<len(c2) and c1[i][0] > c2[j][0]:
                r.increments.append((c2[j][0], c2[j][1]))
                j += 1
            else:
                raise Exception("EquityCurve merge error")
        return r

    def statistics(self, precision=3, extra_stats=()):
        """Calculate most important performance statistics."""
        c = self.   _get_cumsum_seq()
        if len(c)==0:
            return {}
        changes = [i[1] for i in self._seq if i[0]!=0]
        gains = [float(i) for i in changes if i>0]
        if len(gains)==0: print "WARNING: No positive changes in curve."
        losses = [float(i) for i in changes if i<0]
        if len(losses)==0: print "WARNING: No negative changes in curve."
        if len(gains)+len(losses) != 0:
            winrate = float(len(gains))/(len(gains)+len(losses))
        else: winrate = 0
        av_gain = np.mean(gains)
        av_loss = np.mean(losses)
        sd_gain = np.std(gains)
        sd_loss = np.std(losses)
        av = winrate*av_gain + (1-winrate)*av_loss
        sd = np.std(changes)
        if sum(losses) != 0:
            pf = -sum(gains)/sum(losses)
        else: pf = 0
        result = {}
        result['*Final equity'] = c[-1][1]
        result['Changes'] = len(changes)
        result['Points'] = len(c)
        result['Winrate'] = round(winrate, precision)
        result['Avg. gain'] = round(av_gain, precision)
        result['Avg. loss'] = round(av_loss, precision)
        result['Average'] = round(av, precision)
        result['SD'] = round(sd, precision)
        result['SD of gains'] = round(sd_gain, precision)
        result['SD of losses'] = round(sd_loss, precision)
        result['-Sortino ratio'] = round(av/sd_loss, precision)
        result['-Sharpe ratio'] = round(av/sd, precision)
        maxdd = self.maxdd()
        result['-MaxDD'] = maxdd
        result['RF'] = round(c[-1][1]/maxdd, precision)
        result['PF'] = round(pf, precision)
        if 'MC MaxDD' in extra_stats:
            maxdds = self.mc_maxdd_estimate(runs=1000, verbose=False)
            result['MC MaxDD mean'] = np.mean(maxdds)
            result['MC MaxDD sd'] = np.std(maxdds)
            result['MC MaxDD max'] = max(maxdds)
            result['MC MaxDD min'] = min(maxdds)
        return result

    def print_stats(self, precision=3):
        s = self.statistics(precision).items()
        s.sort()
        for i in s:
            print "  "+str(i[0])+":  "+str(i[1])

    def maxdd(self, seq=None):
        """Return maximum drawdown of curve (or other time series if `seq` is supplied)."""
        if seq==None:
            seq = [e for ts, e in self._get_cumsum_seq()]
        m = 0
        maxdd = 0
        for p in seq:
            if p > m:
                m = p
            if m-p > maxdd:
                maxdd = m-p
        return maxdd

    def mc_maxdd_estimate(self, runs=5000, mode=0.005, verbose=True, quantiles=(0.8, 0.95, 0.99)):
        """Monte-Carlo maximum drawdown estimation. Params:
        :runs: specify how many runs to perform;
        :mode: specify
        - how many points should be in one segment, if :mode: >= 1;
        - what fraction of all curve should one segment be, if 0 < :mode: < 1;
        - if :mode: < 0, we will get an error."""
        if verbose: print "running maxdd mc estimation..."
        seq = [i for ts, i in self._seq]
        segments = []
        if mode<0:
            print "E: mode<0"
            return
        elif mode<1:
            breaks = [0]
            while breaks[-1]<len(seq)*(1-mode):
                breaks.append(int(round(breaks[-1]+mode*len(seq)))) ###
            breaks.append(len(seq)-1)
            for i in range(len(breaks)-1):
                segments.append(seq[breaks[i]:breaks[i+1]])
        elif mode==1:
            pass
        else:
            raise Exception("E: :mode:>1 is not implemented yet")
        maxdds = []
        for i in range(runs):
            preturb = []
            while len(preturb)<len(seq):
                if mode != 1:
                    preturb += segments[random.randrange(0, len(segments)-1, 1)]
                else:
                    preturb.append(random.choice(seq))
            maxdds.append(self.maxdd(np.cumsum(preturb)))
        if verbose:
            qs = mquantiles(maxdds, prob=   quantiles)
            print "mc maxdd estimation (%s runs):\n\tmax = %s\n\tmean = %s\n\tsd = %s\n\t%s quantiles = %s" % \
                (runs, max(maxdds), round(np.mean(maxdds), 2), round(np.std(maxdds), 2), quantiles, tuple([round(q, 2) for q in qs]))
        return maxdds

    def plot_mc_maxdd_estimate(self, runs=5000, mode=0.005, bins=100, title='maxdd estimate', **kwargs):
        maxdds = self.mc_maxdd_estimate(runs, mode, **kwargs)
        plt.title("%s, %s trials" % (title, runs))
        plt.ylabel("frequency")
        plt.xlabel("maximum drawdown")
        plt.hist(maxdds, color='green', bins=bins)
        plt.grid(True)
        plt.show()

    def daily_curve(self):
        """ Generates daily EquityCurve based on self. """
        curve = EquityCurve()
        diff = 0
        dt = None
        for ts, inc in self._seq:
            if dt == None:
                dt = ts
            if ts.date() > dt.date():
                curve.add_change(dt, diff)
                diff = 0
            diff += inc
            dt = ts
        curve.add_change(dt, diff)
        return curve

    def plot(self, show=True, title='equity curve', **kwargs):
        """ Line plot of equity dynamics. """
        self.curve.plot(**kwargs)
        plt.title(title)
        plt.grid(True)
        if show:
            plt.show()

    def hist(self, bins=100, mode='l', weighted=False):
        """Plot a histogram of returns distribution."""
        points = [inc for ts, inc in self._seq]
        pos = [p for p in points if p>0]
        neg = [p for p in points if p<0]
        absl = lambda l: [abs(v) for v in l]
        if len(pos)>0 and len(neg)>0:
            img = plt.hist([neg, pos], color=['red', 'green'],
              histtype='stepfilled', bins=bins,
              weights=([absl(neg), pos] if weighted else None),
              )
        elif len(pos)>0:
            img = plt.hist(pos, color='green', histtype='stepfilled', bins=bins)
        else:
            img = plt.hist(neg, color='red', histtype='stepfilled', bins=bins)
        return img

    def plot_ACF(self):
        x = [inc for ts, inc in self._seq]
        cor = np.correlate(x, x, mode='same')
        cor = cor[cor.size/2:cor.size/2+10]
        plt.title("Curve autocorrelation plot")
        plt.grid(True)
        plt.plot(cor)
        plt.show()

    @staticmethod
    def init_from_timeseries(increments):
        curve = EquityCurve()
        curve._seq = zip(increments.index, increments.values)
        return curve

    @staticmethod
    def init_from_trades(trades):
        curve = EquityCurve()
        curve.trades = trades
        var = 0.
        pos = 0.
        for t in trades:
            ts = t[0]
            p = t[1]
            v = t[2]
            if t[3] == 'sell':
                v *= -1
            var -= p*v
            pos += v
            pl = var + pos*p
            curve.add_point(ts, var + pos*p)
        return curve


    @staticmethod
    def _test_changes(n=10):
        c = EquityCurve()
        t = datetime.datetime.now()
        td = datetime.timedelta(seconds=10)
        for i in range(n):
            inc = random.randint(-100, 100)
            c.add_change(t, inc)
            print inc, '->', c.increments[-1]
            t += td
        return c

    @staticmethod
    def _test_init_from_trades(n=10):
        t = datetime.datetime.now()
        td = datetime.timedelta(seconds=10)
        trades = []
        price = 1000
        for i in range(n):
            trd = (t, price, random.randint(-10, 10))
            print trd
            trades.append(trd)
            price += random.randint(-100, 100)
            t += td
        print '----'
        curve = EquityCurve.init_from_trades(trades)
        return curve



def test():
    print 'testing init_from_tables'
    c = EquityCurve._test_init_from_trades()
    return c
