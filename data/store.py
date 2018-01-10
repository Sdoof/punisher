import os
import json
import pandas as pd
from filelock import FileLock

import constants as c
import utils.files
from utils.dates import str_to_date, date_to_str
from utils.encoders import EnumEncoder


class DataStore():
    def __init__(self):
        pass

    def save(self):
        pass

    def load(self):
        pass


class FileStore(DataStore):
    def __init__(self, root):
        self.root = root
        self.initialize()

    def initialize(self):
        if not os.path.exists(self.root):
            os.makedirs(self.root)

    def get_fpath(self, name, file_ext):
        return os.path.join(self.root, name + file_ext)

    def df_to_csv(self, df, name):
        fpath = self.get_fpath(name, c.CSV)
        df.to_csv(fpath, index=True)

    def csv_to_df(self, name, index):
        fpath = self.get_fpath(name, c.CSV)
        df = pd.read_csv(fpath)
        date_cols = self.get_date_cols(df.columns)
        for col in date_cols:
            df[col] = [str_to_date(s) for s in df[col]]
        df.set_index(index, inplace=True)
        return df

    def df_to_json(self, df, name, orient='index'):
        fpath = self.get_fpath(name, c.JSON)
        df_dct = df.to_dict(orient=orient)
        dct = {}
        for key,val in df_dct.items():
            dct[str(key)] = val
        utils.files.save_dct(fpath, dct)

    def json_to_df(self, name, index, orient='index'):
        fpath = self.get_fpath(name, c.JSON)
        df = pd.read_json(fpath, orient=orient)
        date_cols = self.get_date_cols(df.columns)
        for col in date_cols:
            df[col] = [str_to_date(s) for s in df[col]]
        df.index.name = index
        return df

    def save_json(self, name, dct):
        fpath = self.get_fpath(name, c.JSON)
        utils.files.save_dct(fpath, dct)

    def load_json(self, name):
        fpath = self.get_fpath(name, c.JSON)
        return utils.files.load_json(fpath)

    def get_date_cols(self, columns):
        return [
            col for col in columns
            if 'time' in col or 'date' in col
        ]

    def convert_dates(self, columns):
        for col in date_columns:
            df[col] = [str_to_date(s) for s in df[col]]
        return df


class SQLStore(DataStore):
    def __init__(self, endpoint, user, password):
        self.endpoint = endpoint
        self.user = user
        self.password = password

    def get_conn(self):
        return None


FILE_STORE = 'CSV_STORE'

DATA_STORES = {
    FILE_STORE: FileStore
}
