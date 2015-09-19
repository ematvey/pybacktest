# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Set of data-loading helpers """

import pandas as pd


def load_from_yahoo(ticker='SPY', start='1900'):
    """ Loads data from Yahoo. After loading it renames columns to shorter
    format, which is what Backtest expects.

    Set `adjust close` to True to correct all fields with with divident info
    provided by Yahoo via Adj Close field.

    Defaults are in place for convenience. """
    import pandas.io.data
    if isinstance(ticker, list):
        return pd.Panel(
            {t: load_from_yahoo(
                ticker=t, start=start)
             for t in ticker})
    data = pandas.io.data.get_data_yahoo(ticker, start)
    data = data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low',
                                'Close': 'close', 'Volume': 'volume'})
    adj = data['Adj Close'] - data['close']
    data['open'] += adj
    data['high'] += adj
    data['low'] += adj
    data['close'] += adj
    data = data.drop('Adj Close', axis=1)
    return data
