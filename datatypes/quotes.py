import pandas

def get_daily_quotes_yahoo(symbol, start_date, end_date):
    ''' Get daily historical quotes from Yahoo '''
    url = 'http://ichart.yahoo.com/table.csv?s=%s&' % symbol + \
          'd=%s&' % str(int(end_date[4:6]) - 1) + \
          'e=%s&' % str(int(end_date[6:8])) + \
          'f=%s&' % str(int(end_date[0:4])) + \
          'g=d&' + \
          'a=%s&' % str(int(start_date[4:6]) - 1) + \
          'b=%s&' % str(int(start_date[6:8])) + \
          'c=%s&' % str(int(start_date[0:4]))# + \
          #'ignore=.csv'
    return pandas.read_csv(url, index_col=0, parse_dates=True).sort_index()