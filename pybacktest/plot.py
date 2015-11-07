class Plotter(object):
    def __init__(self, blotter):
        self.blotter = blotter

    def _import_plotting(self):
        pass

    def plot_equity(self):
        pass

    def plot_trades(self, subset=None):
        import matplotlib.pylab as pylab

        if subset is None:
            subset = slice(None, None)
        fr = self.blotter.positions.ix[subset]
        tp = self.blotter.trade_price[subset]
        en = tp[fr != 0]
        ex = tp[fr == 0]
        pr = self.blotter.mark_price[subset]

        pylab.plot(en.index, en.values, '^', color='lime', markersize=12,
                   label='entry')
        pylab.plot(ex.index, ex.values, 'v', color='red', markersize=7,
                   label='exit')
        pylab.plot(pr.index, pr.values, color='black')

        pylab.show()

        pylab.title('%s\nTrades for %s' % (self, subset))
