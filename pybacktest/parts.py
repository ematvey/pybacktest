# coding: utf8

# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Essential functions for translating signals into trades.
Usable both in backtesting and production.

"""

import pandas


def signals_to_positions(signals, init_pos=0,
                         mask=('Buy', 'Sell', 'Short', 'Cover')):
    """
    Translate signal dataframe into positions series (trade prices aren't
    specified.
    WARNING: In production, override default zero value in init_pos with
    extreme caution.
    """
    long_en, long_ex, short_en, short_ex = mask  # long enter, long
                                                 # exit, short enter,
                                                 # short exit
    pos = init_pos
    ps = pandas.Series(0., index=signals.index)
    for t, sig in signals.iterrows():
        # check exit signals
        if pos != 0:  # if in position
            if pos > 0 and sig[long_ex] is True:  # if exit long signal
                pos -= sig[long_ex]
            elif pos < 0 and sig[short_ex] is True:  # if exit short signal
                pos += sig[short_ex]
        # check entry (possibly right after exit)
        if pos == 0:
            if sig[long_en] is True:
                pos += sig[long_en]
            elif sig[short_en] is True:
                pos -= sig[short_en]
        ps[t] = pos
    return ps[ps != ps.shift()]


def trades_to_equity(trd):
    """
    Convert trades dataframe (cols [vol, price, pos]) to equity diff series
    """
    psig = trd.pos.apply(lambda x: cmp(x, 0))
    closepoint = psig != psig.shift()
    e = (trd.vol * trd.price).cumsum()[closepoint] - \
        (trd.pos * trd.price)[closepoint]
    e = e.diff()
    e = e.reindex(trd.index).fillna(value=0)
    e[e != 0] *= -1
    return e


def extract_frame(dataobj, ext_mask, int_mask):
    df = {}
    for f_int, f_ext in zip(int_mask, ext_mask):
        obj = dataobj.get(f_ext)
        if isinstance(obj, pandas.Series):
            df[f_int] = obj
        else:
            df[f_int] = None
    if any(map(lambda x: isinstance(x, pandas.Series), df.values())):
        return pandas.DataFrame(df)
    return None


class Slicer(object):
    def __init__(self, target, obj):
        self.target = target
        self.__len__ = obj.__len__
    def __getitem__(self, x):
        return self.target(x)
