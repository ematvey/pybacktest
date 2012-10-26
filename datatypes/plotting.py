import matplotlib.pyplot as plt
from matplotlib.finance import candlestick
from matplotlib.dates import date2num

def plot_bars(bars, ax=None, show=False):
    t = [date2num(b.timestamp) for b in bars]
    o = [b.O for b in bars]
    h = [b.H for b in bars]
    l = [b.L for b in bars]
    c = [b.C for b in bars]
    ax = plt.figure().add_subplot(111) if not ax else ax
    candlestick2(ax, o, c, h, l, width=2, colorup='g', colordown='r', alpha=0.75)
    if show:
        plt.show()
    return ax
