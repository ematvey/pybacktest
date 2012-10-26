
import csv
import datetime
from decimal import Decimal
from .datapoint import Bar, Tick

import logging
_log = logging.getLogger(__name__)
_log.setLevel(logging.DEBUG)

def read_bars(*args):
    """Format: <DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL> (Finam's last)"""
    bars = []
    total = 0
    for f in args:
        bs = []
        data = csv.reader(open(f, 'rb'), delimiter=';')
        data.next() # skip headers
        for l in data:
            bs.append(Bar(*[float(v) for v in l]))
        _log.info("Loaded %s with %s bars", f, len(bs))
        bars.append(bs)
    return bars


def read_ticks(*args):
    """Format: <TICKER>;<DATE>;<TIME>;<LAST>;<VOL>"""
    ticks = []
    total = 0
    for f in args:
        _log.debug("Loading ticks from %s", f)
        data = csv.reader(open(f, 'rb'), delimiter=',')
        data = list(data)
        _log.info("Loaded file %s", f)
        for l in data:
            ticks.append(Tick(*[float(v) for v in [l[1], l[2], l[3], l[4]]]))
        _log.info("Loaded %s with %s ticks", f, len(ticks) - total)
        total = len(ticks)
    return ticks
