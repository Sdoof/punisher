import datetime

import utils
from . import ohlcv


class DataFeed():
    def __init__(self, fpath, start=None, end=None):
        self.fpath = fpath
        self.start = start
        self.end = end
        self.prior_time = None
        self.feed = None
                           
    def initialize(self):
        print("Loading feed:", self.fpath)
        if self.start is None:
            self.start = datetime.datetime(1, 1, 1, 1, 1)
        print("START", self.start)
        self.prior_time = self.start - datetime.timedelta(minutes=1)
        print("PRIOR", self.prior_time)
    
    def update(self):
        pass

    def history(self, t_minus=0):
        """Return t_minus rows from feed
        Which should represent the latest dates
        """
        return self.feed.iloc[-t_minus:]

    def next(self, refresh=False):
        if refresh: 
            self.end = datetime.datetime.utcnow()
            self.update()
        data = self.feed[self.feed.index > utils.dates.utc_to_epoch(self.prior_time)]
        if len(data) > 0:
            row = data.iloc[0]
            self.prior_time = row['time_utc']
            return row
        print("No data after prior poll:", self.prior_time)
        return None
    
    def __len__(self):
        return len(self.feed)

    
class CSVDataFeed(DataFeed):
    def __init__(self, fpath, start=None, end=None):
        super().__init__(fpath, start, end)

    def initialize(self):
        super().initialize()
        self.update()
    
    def update(self):
        self.feed = ohlcv.load_chart_data_from_file(
            self.fpath, self.prior_time, self.end)


class ExchangeDataFeed(DataFeed):
    def __init__(self, exchange, coins, market, 
                 period, fpath, start, end=None):
        super().__init__(fpath, start, end)
        self.exchange = exchange
        self.coins = coins
        self.market = market
        self.period = period

    def initialize(self):
        super().initialize()
        self.update()
        
    def update(self):
        self._download(self.prior_time, self.end)
        
        if len(self.coins) > 1:
            self.feed = ohlcv.load_multi_coin_data(
                self.exchange.id, self.coins, 
                self.market, self.period, 
                self.start, self.end)
        else:
            coin_fpath = ohlcv.get_price_data_fpath(
                self.coins[0], self.market, 
                self.exchange.id, self.period)
            self.feed = ohlcv.load_chart_data_from_file(
                coin_fpath, self.start, self.end)
        
    def _download(self, start, end):
        ohlcv.download_chart_data(
            self.exchange, self.coins, 
            self.market, self.period, 
            start, end)