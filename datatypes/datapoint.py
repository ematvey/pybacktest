# coding: utf8

import datetime
from decimal import Decimal

base_fields = ('O', 'H', 'L', 'C', 'V')
readonly_fields = ('Date', 'Time', 'date', 'time', 'TS', 'ts')
fields = ('O', 'H', 'L', 'C', 'V', 'timestamp', 'contract')
repr_fields = base_fields


class Datapoint(dict):
    ''' Market datapoint (e.g. tick or bar) '''
    
    def __init__(self, **kwargs):
        [setattr(self, k, v) for k, v in kwargs.iteritems() if k in fields]
    
    def __reprstring(self):
        s = ''
        for f in repr_fields:
            if hasattr(self, f):
                if len(s) != 0:
                    s += ' / '
                s += '%s %s' % (f, str(getattr(self, f)))
        return s
    
    def __repr__(self):
        return '<(%s)  %s>' % (self.timestamp, self.__reprstring())
    
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)
    
    def __setattr__(self, name, value):
        if not name in readonly_fields:
            self[name] = value
        else:
            raise Exception("Attribute '%s' is read-only." % name)
            
    @property
    def fields(self):
        return [f for f in fields if hasattr(self, f)]
    
    @property
    def Date(self):
        ''' Legacy compatibility conversion. '''
        return int(self.timestamp.strftime("%Y%m%d"))
    
    @property
    def Time(self):
        ''' Legacy compatibility conversion. '''
        if self.timestamp.microsecond == 0:
            return int(self.timestamp.strftime("%H%M%S"))
        else:
            return float(self.timestamp.strftime("%H%M%S.%f"))
    
    @property
    def TS(self):
        return self.timestamp
    
    def decimalize(self):
        """Convert all float attributes to decimals with 5-point precision."""
        for k, v in self.__dict__.iteritems():
            if isinstance(float, v):
                setattr(self, k, Decimal(v).quantize('1.00000'))


## -------------------------------------------------------
# Compatibility classes

class bar(Datapoint):
    pass
class Bar(bar):
    def __init__(self, Date, Time, O, H, L, C, V):
        self.timestamp = datetime.datetime.strptime(str(int(Date))+" "+str(int(Time)), "%Y%m%d %H%M%S")
        self.O = float(O)
        self.H = float(H)
        self.L = float(L)
        self.C = float(C)
        self.V = float(V)
class tick(Datapoint):
    pass
class Tick(tick):
    def __init__(self, Date, Time, C, V, OI=None):
        self.timestamp = datetime.datetime.strptime(str(int(Date))+" "+str(int(Time)), "%Y%m%d %H%M%S")
        self.C = float(C)
        self.V = float(V)
        if OI != None:
            self.OI = OI

## --------------------------------------------------------

class BarFrame(object):
    def __init__(self, datapoints):
        self.frame = data.BarsToDataframe(datapoints)
    def __repr__(self):
        return '<BarFrame %s .. %s>' % (self.frame['timestamp'][0].date(), 
            self.frame['timestamp'][-1].date())
    @property
    def datapoints(self):
        return data.BarsFromDataframe(self.frame)
        
DatapointContainer = BarFrame
