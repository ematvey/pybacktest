import pandas
import sys
from pybacktest.backtest import Backtest


def iter_verify(strategy_fn, data, window_size):
    """
    Verify vectorized pandas backtest iteratively by running it
    in sliding window, bar-by-bar.

    NOTE: depreciated, use `verify` now.
    """
    sp = None
    mis_cur = {}
    mis_prev = {}
    print('iterative verification')
    for i in range(window_size, len(data)):
        s = Backtest(strategy_fn(data.iloc[i-window_size:i])).signals
        if (not sp is None) and (sp != s.iloc[-2]).any():
            ix = data.index[i]
            mis_prev[ix] = sp
            mis_cur[ix] = s.iloc[-2]
        sp = s.iloc[-1]
        prg = round(((float(i) - window_size) / (len(data) - window_size)) * 100, 1)
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
        print('valid')


def frontal_iterative_signals(strategy_fn, data, window_size, verbose=True):
    front = []
    p_prg = None
    for i in range(window_size, len(data)):
        data_subset = data.iloc[i - window_size : i]
        last_sig = Backtest(strategy_fn(data_subset)).signals.iloc[-1]
        front.append(last_sig)
        if verbose:
            prg = round(((float(i) - window_size) / (len(data) - window_size)) * 100, 1)
            if p_prg != prg:
                sys.stdout.write(' \r%s%% done' % prg)
                sys.stdout.flush()
                p_prg = prg
    return pandas.DataFrame(front)


def verify(strategy_fn, data, window_size, verbose=True):
    """
    Verify vectorized pandas backtest iteratively by running it
    in sliding window, bar-by-bar.
    """
    fsig = frontal_iterative_signals(strategy_fn, data, window_size, verbose)
    bsig = Backtest(strategy_fn(data)).signals.reindex(fsig.index)
    comp = fsig.ix[(fsig == bsig).T.all() == False]
    if len(comp) != 0:
        if verbose:
            sys.stdout.write('\rverification did not pass\nreturning dataframe with mismatches')
            sys.stdout.flush()
        return comp
    elif verbose:
        sys.stdout.flush()
        sys.stdout.write('\rverification passed')
