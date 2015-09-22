# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Set of data-loading helpers """

import pandas
from pandas.io.data import get_data_yahoo


def load_from_yahoo(ticker='SPY', start='1900'):
    """
    Loads data from Yahoo.
    After loading it renames columns to shorter format, which is what Backtest expects.
    Adjust all price fields by dividend yield.
    """
    data = get_data_yahoo(ticker, start)
    data = data.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low',
                                'Close': 'close', 'Volume': 'volume'})
    adj = data['Adj Close'] / data['close']
    data[['open', 'high', 'low', 'close']] *= adj
    data = data.drop('Adj Close', axis=1)
    return data
