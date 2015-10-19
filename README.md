# pybacktest
Simple yet powerful backtesting framework in python/pandas.

### Updates

**18.10.2015**

Development of v0.2 is actively uderway in branch `v0.2`. This is a complete rewrite and nowhere near ready, but I believe it is already better then current master in many ways. Documentation/examples is non-existent though.

**21.05.2015**

This package has long been abandoned, but now I am planning to move it to version 0.2. Main goals are:
 - Smarter handling of possible backtest initialization arguments, such as different ways to specify signals, price data and such.
 - Better multi-asset backtest capabilites.
 - Order type specification. Currently there are two ways to specify backtest: simply pass signals and get next-bar-market-on-open backtest, or add trade prices and get stop order-like execution, but without proper possibility of trade checking. You will still be able to do these things, with added option to futher customize execution and simulate more production-like environment.

### About
It allows user to specify trading strategies using full power of pandas while hiding all the plumbing. Resulting strategy code can be used both in research and production setting.

Strategies could be tested as simple this:
```python
def strategy(data):
    ms = pandas.rolling_mean(data.close, 50)
    ml = pandas.rolling_mean(data.close, 100)
    return {
        'long_entry': (ms > ml) & (ms.shift() < ml.shift()),
        'short_entry': (ms < ml) & (ms.shift() > ml.shift()),
    }
backtest = pybacktest.Backtest(data, strategy)
```

## Installation
```
git clone https://github.com/ematvey/pybacktest.git
cd pybacktest
python setup.py install
```
If you don't install it in virtualenv, you might need to prepend last line with sudo.

## Tutorial
Tutorials are provided as ipython notebooks in folder *examples*. You run it from cloned repo or [watch via nbviewer](http://nbviewer.ipython.org/urls/raw.github.com/ematvey/pybacktest/master/examples/tutorial.ipynb).

## Status
Single-security backtester is ready. Multi-security testing could be implemented by running single-sec backtests and then combining equity. Later we will add easier way.
