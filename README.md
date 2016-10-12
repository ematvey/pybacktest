# pybacktest
Simple yet powerful backtesting framework in python/pandas.

Currently I don't plan to continue working on this project.

### About
It allows user to specify trading strategies using full power of pandas, at the same time hiding all boring things like manually calculating trades, equity, performance statistics and creating visualizations. Resulting strategy code is usable both in research and production setting.

Strategies could be defined as simple this:
```python
ms = pandas.rolling_mean(ohlc.C, 50)
ml = pandas.rolling_mean(ohlc.C, 100)
buy = cover = (ms > ml) & (ms.shift() < ml.shift())
sell = short = (ms < ml) & (ms.shift() > ml.shift())
```

And then tested like this:
`pybacktest.Backtest(locals())`

We use it in our research and production operations.

## Installation
```
pip install git+https://github.com/ematvey/pybacktest.git
```
If you don't install it in virtualenv, you might need to prepend last line with sudo.

## Tutorial
Tutorials are provided as ipython notebooks in folder *examples*. You run it from cloned repo or [watch via nbviewer](http://nbviewer.ipython.org/urls/raw.github.com/ematvey/pybacktest/master/examples/tutorial.ipynb).

## Status
Single-security backtester is ready. Multi-security testing could be implemented by running single-sec backtests and then combining equity. Later we will add easier way.
