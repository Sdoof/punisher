import copy
import json
import uuid
from datetime import datetime
from enum import Enum, unique

from punisher.portfolio.asset import Asset
from punisher.utils.dates import str_to_date, date_to_str
from punisher.utils.encoders import EnumEncoder

from .errors import OrderingError


@unique
class OrderStatus(Enum):
    CREATED = "Order not yet submitted to exchange"
    OPEN = "Order created on exchange, but not completely filled"
    FILLED = "Order completely filled on exchange"
    CANCELED = "Order canceled by user"
    FAILED = "Order failed/rejected by exchange. Will retry"
    KILLED = "Order rejected by exchange. Will not retry"

    def __repr__(self):
        return str(self.name)


@unique
class OrderType(Enum):
    LIMIT_BUY = {'type':'limit', 'side':'buy', 'desc':''}
    LIMIT_SELL = {'type':'limit', 'side':'sell', 'desc':''}
    MARKET_BUY = {'type':'market', 'side':'buy', 'desc':''}
    MARKET_SELL = {'type':'market', 'side':'sell', 'desc':''}
    STOP_LIMIT_BUY = 4
    STOP_LIMIT_SELL = 5

    @classmethod
    def from_type_side(self, type_, side):
        # TODO: Add more order types
        order_type_map = {
            'limit_buy': OrderType.LIMIT_BUY,
            'limit_sell': OrderType.LIMIT_SELL,
            'market_buy': OrderType.MARKET_BUY,
            'market_sell': OrderType.MARKET_SELL,
        }
        key = type_.lower() + '_' + side.lower()
        return order_type_map[key]

    @classmethod
    def buy_types(self):
        return set([
            OrderType.LIMIT_BUY,
            OrderType.MARKET_BUY,
            OrderType.STOP_LIMIT_BUY
        ])

    @classmethod
    def sell_types(self):
        return set([
            OrderType.LIMIT_SELL,
            OrderType.MARKET_SELL,
            OrderType.STOP_LIMIT_SELL
        ])

    @property
    def type(self):
        return self.value['type']

    @property
    def side(self):
        return self.value['side']

    def is_buy(self):
        return self in self.buy_types()

    def is_sell(self):
        return self in self.sell_types()

    def __repr__(self):
        return str(self.name)


class Order():
    __slots__ = [
        "id", "exchange_id", "exchange_order_id", "asset", "price",
        "quantity", "filled_quantity", "order_type", "status",
        "created_time", "opened_time", "filled_time", "canceled_time",
        "fee", "attempts", "trades", "error"
    ]

    def __init__(self, exchange_id, asset, price, quantity, order_type,
                    created_time):
        self.id = self.make_id()
        self.exchange_id = exchange_id
        self.exchange_order_id = None
        self.asset = asset
        self.price = price
        self.quantity = quantity
        self.filled_quantity = 0.0
        self.order_type = self.set_order_type(order_type)
        self.status = OrderStatus.CREATED
        self.created_time = created_time
        self.opened_time = None
        self.filled_time = None
        self.canceled_time = None
        self.fee = 0.0
        self.attempts = 0
        self.trades = []
        self.error = None

    def get_new_trades(self, last_update_time):
        new_trades = []
        for trade in self.trades:
            print("Inspecting trade times...")
            print("trade time", trade.trade_time)
            print("last_update_time", last_update_time)
            if trade.trade_time >= last_update_time:
                new_trades.append(trade)
        return new_trades

    def set_order_type(self, order_type):
        assert order_type in OrderType
        self.order_type = order_type
        return self.order_type

    def set_status(self, status):
        assert status in OrderStatus
        self.status = status

    def to_dict(self):
        dct = {
            name: getattr(self, name)
            for name in self.__slots__
        }
        del dct['asset']
        dct['symbol'] = self.asset.symbol
        dct['status'] = self.status.name
        dct['order_type'] = self.order_type.name
        dct['error'] = None if self.error is None else self.error.to_dict()
        dct['created_time'] = date_to_str(self.created_time)
        dct['opened_time'] = date_to_str(self.opened_time)
        dct['filled_time'] = date_to_str(self.filled_time)
        dct['canceled_time'] = date_to_str(self.canceled_time)
        dct['trades'] = [trade.to_dict() for trade in self.trades]
        return dct

    @classmethod
    def from_dict(self, d):
        order = Order(
            exchange_id=d['exchange_id'],
            asset=Asset.from_symbol(d['symbol']),
            price=d['price'],
            quantity=d['quantity'],
            order_type=OrderType[d['order_type']],
            created_time=str_to_date(d['created_time'])
        )
        order.id = d['id']
        order.exchange_order_id = d['exchange_order_id']
        order.filled_quantity = d['filled_quantity']
        order.status = OrderStatus[d['status']]
        order.opened_time = str_to_date(d['opened_time'])
        order.filled_time = str_to_date(d['filled_time'])
        order.canceled_time = str_to_date(d['canceled_time'])
        order.attempts = d['attempts']
        order.fee = d['fee']
        order.error = OrderingError.from_dict(d['error'])
        return order

    def to_json(self):
        dct = self.to_dict()
        return json.dumps(dct, cls=EnumEncoder, indent=4)

    @classmethod
    def from_json(self, json_str):
        dct = json.loads(json_str)
        return self.from_dict(dct)

    def make_id(self):
        return uuid.uuid4().hex

    def __repr__(self):
        return self.to_json()


class ExchangeOrder():
    __slots__ = [
        "ex_order_id", "exchange_id", "asset", "quantity", "price",
        "filled_quantity", "order_type", "status", "opened_time",
        "filled_time", "canceled_time", "fee", "trades"
    ]

    def __init__(self, ex_order_id, exchange_id, asset, quantity,
                 price, filled_quantity, order_type, status):
        self.ex_order_id = ex_order_id
        self.exchange_id = exchange_id
        self.asset = asset
        self.quantity = quantity
        self.price = price
        self.filled_quantity = filled_quantity
        self.order_type = self.set_order_type(order_type)
        self.status = self.set_status(status)
        self.opened_time = None
        self.filled_time = None
        self.canceled_time = None
        self.fee = {}
        self.trades = []

    def set_order_type(self, order_type):
        assert order_type in OrderType
        self.order_type = order_type
        return self.order_type

    def set_status(self, status):
        assert status in OrderStatus
        self.status = status
        return self.status

    def to_dict(self):
        dct = {
            name: getattr(self, name)
            for name in self.__slots__
        }
        dct['id'] = self.ex_order_id
        dct['amount'] = self.quantity
        dct['filled'] = self.filled_quantity
        dct['symbol'] = self.asset.symbol
        dct['datetime'] = date_to_str(self.opened_time)
        dct['side'] = self.order_type.side
        dct['type'] = self.order_type.type
        dct['trades'] = [trade.to_dict() for trade in self.trades]

        del dct['ex_order_id']
        del dct['quantity']
        del dct['filled_quantity']
        del dct['asset']
        del dct['datetime']
        del dct['order_type']

        dct['status'] = self.status.name
        dct['filled_time'] = date_to_str(self.filled_time)
        dct['canceled_time'] = date_to_str(self.canceled_time)
        return dct

    @classmethod
    def from_dict(self, d):
        order = ExchangeOrder(
            ex_order_id = d['id'],
            exchange_id=d['exchange_id'],
            asset=Asset.from_symbol(d['symbol']),
            price=d['price'],
            quantity=d['amount'],
            filled_quantity=d['filled'],
            order_type=OrderType.from_type_side(d['type'], d['side']),
            status=OrderStatus[d['status']],
        )
        order.opened_time = str_to_date(d['datetime'])
        order.filled_time = str_to_date(d.get('filled_time'))
        order.canceled_time = str_to_date(d.get('canceled_time'))
        order.fee = d.get('fee', {})
        return order

    def to_json(self):
        dct = self.to_dict()
        return json.dumps(dct, cls=EnumEncoder, indent=4)

    @classmethod
    def from_json(self, json_str):
        dct = json.loads(json_str)
        return self.from_dict(dct)

    def __repr__(self):
        return self.to_json()


def buy_order_types():
    return [OrderType.LIMIT_BUY,
            OrderType.MARKET_BUY,
            OrderType.STOP_LIMIT_BUY]

def sell_order_types():
    return [OrderType.LIMIT_SELL,
            OrderType.MARKET_SELL,
            OrderType.STOP_LIMIT_SELL]
