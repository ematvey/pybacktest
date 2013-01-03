import datetime
import pandas

from .datapoint import bar


yahoo_tpl = {'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close',
             'v': 'Volume', 'ac': 'Adj Close'}

finam_tpl = {'o': '<OPEN>', 'h': '<HIGH>', 'l': '<LOW>', 'c': '<CLOSE>',
            'v': '<VOL>'}

def pandas_bars_wrap(dataframe, template=yahoo_tpl):
    bars = []
    tpl = template
    return [bar(
                timestamp=ts.to_pydatetime(),
                O=row[tpl['o']],
                H=row[tpl['h']],
                L=row[tpl['l']],
                C=row[tpl['c']],
                V=row[tpl['v']],
        ) for ts, row in dataframe.iterrows()]