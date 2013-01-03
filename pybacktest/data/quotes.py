import pandas
import urllib
import datetime

finam_symbols = urllib.urlopen('http://www.finam.ru/cache/icharts/icharts.js').readlines()

def get_daily_quotes_yahoo(symbol, start_date, end_date):
    ''' Get daily historical quotes from Yahoo '''
    url = 'http://ichart.yahoo.com/table.csv?s=%s&' % symbol +\
          'd=%s&' % str(int(end_date[4:6]) - 1) +\
          'e=%s&' % str(int(end_date[6:8])) +\
          'f=%s&' % str(int(end_date[0:4])) +\
          'g=d&' +\
          'a=%s&' % str(int(start_date[4:6]) - 1) +\
          'b=%s&' % str(int(start_date[6:8])) +\
          'c=%s&' % str(int(start_date[0:4]))# + \
    #'ignore=.csv'
    return pandas.read_csv(url, index_col=0, parse_dates=True).sort_index()

def get_finam_code(symbol):
    s_id = finam_symbols[0]
    s_code = finam_symbols[2]
    names = s_code[s_code.find('[\'')+1:s_code.find('\']')].split('\',\'')
    ids = s_id[s_id.find('[')+1:s_id.find(']')].split(',')
    if (symbol in names):
        symb_id = names.index(symbol)
        return int(ids[symb_id])
    else:
        print "%s not found\r\n" % symbol
    return 0

def get_daily_quotes_finam(symbol, start_date='20070101', end_date=datetime.date.today().strftime('%Y%m%d'), period=8):
    start_date = datetime.datetime.strptime(start_date, "%Y%m%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y%m%d").date()
    symb = get_finam_code(symbol)
    url = 'http://195.128.78.52/table.csv?d=d&market=1&f=table&e=.csv&dtf=1&tmf=1&MSOR=0&mstime=on&mstimever=1&sep=3&sep2=1&at=1&datf=5'+\
                '&p=' +str(period)+\
                '&em='+str(symb)+\
                '&df='+str(start_date.day)+\
                '&mf='+str(start_date.month-1)+\
                '&yf='+str(start_date.year)+\
                '&dt='+str(end_date.day)+\
                '&mt='+str(end_date.month-1)+\
                '&yt='+str(end_date.year)+\
                '&cn='+symbol
    return pandas.read_csv(url, index_col=0, parse_dates=True, sep=';').sort_index()
