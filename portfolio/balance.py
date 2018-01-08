from enum import Enum, unique

import constants as c
import config as cfg

from .asset import get_symbol

FREE = "free"
USED = "used"
TOTAL = "total"

class Balance():
    def __init__(self, cash_currency=c.BTC, starting_cash=1.0):
        self.free = {cash_currency: starting_cash}
        self.used = {cash_currency: 0.0}
        self.total = {cash_currency: 0.0}

    @property
    def currencies(self):
        return self.total.keys()

    def get(self, currency):
        return {
            FREE: self.free[currency],
            USED: self.used[currency],
            TOTAL: self.total[currency],
        }

    def update(self, currency, free, used):
        self.free[currency] = free
        self.used[currency] = used
        self.total = self.free[currency] + self.used[currency]


    def to_dict(self, d):
        return {
            FREE: self.free[currency],
            USED: self.used[currency],
            TOTAL: self.total[currency],
        }

    @classmethod
    def from_dict(self, dict):
        self.free = balance[FREE]
        self.used = balance[USED]
        self.total = balance[TOTAL]


@unique
class BalanceType(Enum):
    FREE = "Quantity available for trading"
    USED = "Quantity currently invested"
    TOTAL = "Free + Used"



## Helpers

def get_total_value(balance, cash_currency, exchange_rates):
    cash_value = 0.0
    for currency in balance.currencies:
        symbol = get_symbol(currency, cash_currency)
        quantity = balance.get(currency)[TOTAL]
        rate = exchange_rates[symbol]
        cash_value += quantity * exchange_rate
    return cash_value
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           
