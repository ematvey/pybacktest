# part of pybacktest package: https://github.com/ematvey/pybacktest

""" Set of pandas.Series processing functions, mimicing AmiBroker's built-ins
to help translate strategies from AmiScript.

Note that most AmiScript's built-in funtions have more advanced native analogs
in pandas. Funcs like that will not be replicated here.

"""

import pandas


__all__ = ['ExRem', 'BarsSince', 'TimeNum', 'DateNum']


def ExRem(array1, array2):
    """ Removes excessive signals from array1 until first True in array2 occurs.

    Reference implementation:
    http://www.amibroker.com/guide/afl/afl_view.php?name=timenum
    """
    assert array1.index.equals(array2.index), 'Indices do not match'
    array = pandas.Series(False, dtype=bool, index=array1.index)
    i = 0
    while i < len(array1):
        if array1[i]:
            array[i] = True
            for j in range(i, len(array2)):
                if array2[j]:
                    break
            i = j
        i += 1
    return array.fillna(value=False)


def BarsSince(x):
    """ Counts number of periods since last True occured.

    Reference implementation:
    http://www.amibroker.com/guide/afl/afl_view.php?name=barssince

    """
    ret = pandas.Series(dtype=float, index=x.index)
    ret[x] = 0
    ret[x == False] = 1
    cs = ret.cumsum()
    return cs - cs[x].reindex(cs.index).ffill()


def TimeNum(x):
    """ Returns timecode for each element.
    
    Reference implementation:
    http://www.amibroker.com/guide/afl/afl_view.php?name=timenum
    
    """
    timecode = [x.hour * 10000 + x.minute * 100 + x.second for x in [x.time() for x in x.index]]
    return pandas.Series(timecode, index=x.index)


def DateNum(x):
    """ Returns datecode for each element.

    Reference implementation:
    http://www.amibroker.com/guide/afl/afl_view.php?name=datenum

    """
    datecode = [10000 * (x.year - 1900) + 100 * x.month + x.day for x in [x.date() for x in x.index]]
    return pandas.Series(datecode, index=x.index)
