import csv
import datetime
from .equity import EquityCurve

def equity_ami(filename):
    ''' Parse AmiBroker's trade list into EquityCurve.
    Tested on AmiBroker 5.50.
    '''
    r = csv.reader(open(filename))
    h = r.next()
    di = h.index('Date')
    ei = h.index('Cum. Profit')
    eq = EquityCurve()
    for l in r:
        dt = datetime.datetime.strptime(l[di], '%d.%m.%Y %H:%M:%S')
        eq.add_point(dt, float(l[ei]))
    return eq
        
