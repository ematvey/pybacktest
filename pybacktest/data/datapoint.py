# coding: utf8

import datetime
from decimal import Decimal


class Datapoint(object):
    ''' Market datapoint (e.g. tick or bar) '''

    _fields = ('timestamp', 'contract', 'O', 'H', 'L', 'C', 'V', 'OI')
    #_readonly_fields = ('Date', 'Time', 'date', 'time', 'TS', 'ts')
    _repr_fields = _fields

    def __init__(self, *args, **kwargs):
        self._dict = {}
        # item calls redirection
        self.__setitem__ = self._dict.__setitem__
        self.__getitem__ = self._dict.__getitem__
        #
        self.init(self, **kwargs)

    def init(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            if k in self._fields:
                self._dict[k] = v

    def _reprstring(self):
        s = ''
        for f in self._repr_fields:
            if f in self._dict:
                if len(s) != 0:
                    s += ', '
                s += '%s=%s' % (f, str(getattr(self, f)))
        return s

    def __repr__(self):
        return 'Datapoint(%s)' % self._reprstring()
    
    #def __getitem__(self, name):
    #    #if not hasattr(self, '_dict'):
    #    #    self._dict = {}
    #    return self._dict[name]

    #def __setitem__(self, name, value):
    #    #if not hasattr(self, '_dict'):
    #    #    self._dict = {}
    #    self._dict[name] = value

    def __getattr__(self, name):
        #if not hasattr(self, '_dict'):
        #    self._dict = {}
        if name == '_dict':
            import ipdb; ipdb.set_trace()
        return self._dict[name]

    def __setattr__(self, name, value):
        #if not hasattr(self, '_dict'):
        #    self._dict = {}
        if name != '_dict':
            self._dict[name] = value
        else:
            return object.__setattr__(self, name, value)

    @property
    def fields(self):
        return [f for f in self._fields if hasattr(self, f)]
    
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
    def __repr__(self):
        return 'Bar(%s)' % self._reprstring()
class Bar(bar):
    def __init__(self, Date, Time, O, H, L, C, V, **kwargs):
        super(Bar, self).__init__()
        self.timestamp = datetime.datetime.strptime(str(int(Date))+" "+str(int(Time)), "%Y%m%d %H%M%S")
        self.O = float(O)
        self.H = float(H)
        self.L = float(L)
        self.C = float(C)
        self.V = float(V)
class tick(Datapoint):
    def __repr__(self):
        return 'Bar(%s)' % self._reprstring()    
class Tick(tick):
    def __init__(self, Date, Time, C, V, OI=None):
        super(Tick, self).__init__()
        self.timestamp = datetime.datetime.strptime(str(int(Date))+" "+str(int(Time)), "%Y%m%d %H%M%S")
        self.C = float(C)
        self.V = float(V)
        if OI != None:
            self.OI = OI