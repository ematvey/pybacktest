# PyBacktest
Compact framework for backtesting trading strategies.

## Installation
Simply clone and import modules as you need them. To get a sense of things study test stripts in root folder. Setup via distutils will be added later.

## Features of this version
 * Ready-to-use one-asset backtesting and optimizing
 * Not too hard to implement multi-asset backtesting
 * Full Equity calculation calculation with various performance statistics such as PF, Sharpe, Sortino, MC maximum drawdown estimate, etc
  * Export equity curve into pandas
  * Easy to extend performance statistics set
 * E-ratio entry analysis
 * Generate equity curve class from AmiBroker's tradelist

## Examples
Run `python test.py` to backtest simple MA crossover strategy or `python test_opt.py` to to try optimization. You might have to install some dependencies.

## Basic workflow
### Simple backtest
You will need a dataset, represented as iterable over datapoints, or iterable over iterables over datapoints (i.e. list of lists of bars, like in future chain). Datapoint could be any format you desire, but current implementation assumes that datapoints at least have attribute `C` for close price. Easy to change that though.

Next, implement your trading strategy. This could be inheriting PositionalStrategy class and implementing abstract method `step`. This method will be recieving datapoints one-by-one from backtester, processing them and trading via `change_position` method. If you are going to use PositionalStrategy, note that it makes some additional assumptions about data (see code).

When you're ready, create SimpleBacktester object with your dataset and strategy class object as arguments (you can pass args and kwargs for strategy instantiation too). Backtester will run automatically.

After it is finished equity curves will be in `full_curve`, `trades_curve` attributes.

### Optimization
Optimization is performed via `Optimizer` class. Mostly it mirrors `Backtester`. Create instance by supplying backtester class, data and strategy class. Add optimization params via `add_opt_params` as usual (params will be supplied as kwargs in strategy's constructor). Finally, `run` optimizer with target statistics as argument. That's about it.

### Multi-asset backtest
This requires a bit more tinkering but basically you will need to:

 * Override backtester by making separate EquityCalculator for every asset, changing `_trade` and `_matching_callback`
 * Write your own Strategy class
 * After testing is complete, merge EquityCurves for individual asset into one final curve

Native support for multi-asset backtesting will be implemented later.

## API
See docstrings in code for documentation