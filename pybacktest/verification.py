import pandas
import sys
from . import Backtest

def iter_verify(strategy_fn, data, window_size):
    '''
    Verify vectorized pandas backtest iteratively by running it
    in sliding window, bar-by-bar.

    '''
    sp = None
    mis_cur = {}
    mis_prev = {}
    prg_d = 0.
    print 'iterative verification'
    for i in range(window_size, len(data)):
        s = Backtest(strategy_fn(data.iloc[i-window_size:i])).signals
        if (not sp is None) and (sp != s.iloc[-2]).any():
            ix = data.index[i]
            mis_prev[ix] = sp
            mis_cur[ix] = s.iloc[-2]
        sp = s.iloc[-1]
        prg = round(float(i) / (len(data) - window_size) * 100, 1)
        sys.stdout.write(' \r%s%% done' % prg)
        sys.stdout.flush()
    df = pandas.Panel(
        {'cur': pandas.DataFrame(mis_cur),
         'prev': pandas.DataFrame(mis_prev)}
    ).to_frame().swaplevel(0, 1).sort()
    df = df.ix[df['cur'] != df['prev']]
    if len(df):
        return df
    else:
        return 'valid'
