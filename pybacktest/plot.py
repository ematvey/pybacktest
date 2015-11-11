# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

class Plotter(object):
    class Slicer(object):
        def __init__(self, target):
            self.target = target

        def __getitem__(self, x):
            return self.target(x)

    def __init__(self, blotter):
        self.blotter = blotter

        self.trdplot = self.Slicer(self.trades)

    def equity(self, **kwa):
        (self.blotter.continuous_returns + 1).cumprod().plot(**kwa)

    def trades(self, subset=None):
        import matplotlib.pylab as pylab

        if subset is None:
            subset = slice(None, None)

        fr = self.blotter.positions.ix[subset]
        tp = self.blotter.trade_price.ix[subset]
        ens = tp[fr != 0]
        exs = tp[fr == 0]
        pr = self.blotter.mark_price.ix[subset]
        pylab.plot(ens.index, ens.values, '^', color='lime', markersize=12,
                   label='entry')
        pylab.plot(exs.index, exs.values, 'v', color='red', markersize=7,
                   label='exit')
        pylab.plot(pr.index, pr.values, color='black')
        pylab.legend()
        pylab.show()
