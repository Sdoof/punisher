import json
import datetime
import copy

from punisher.utils.encoders import EnumEncoder
from punisher.utils.dates import Timeframe

from punisher.trading.trade import TradeSide
from .performance import PerformanceTracker
from .position import Position


class Portfolio():
    """
    Attributes:
      - starting_cash (float): Amount of cash
      - perf_tracker (PerformanceTracker): Records PnL for each period
      - positions (list): list of existing Positions

    Reference Impls:
    https://github.com/quantopian/zipline/blob/master/zipline/protocol.py#L143
    """

    def __init__(self, starting_cash, perf_tracker, positions=None):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.perf = perf_tracker
        self.positions = [] if positions is None else positions

    def update(self, current_time, new_trades, latest_prices):
        self.update_positions(new_trades)
        self.update_position_prices(latest_prices)
        self.perf.add_period(current_time, self.cash, self.positions)

    def update_positions(self, new_trades):
        for trade in new_trades:
            pos = self.get_position(trade.asset)
            if pos is None:
                pos = Position(
                        asset=trade.asset,
                        quantity=trade.quantity,
                        cost_price=trade.price,
                        fee=trade.fee
                    )
                self.positions.append(pos)
                quantity = trade.quantity
            else:
                if trade.side == TradeSide.SELL:
                    quantity = -trade.quantity
                else:
                    quantity = trade.quantity
                pos.update(quantity, trade.price, trade.fee)
            self.cash -= (quantity * trade.price) - trade.fee

    def update_position_prices(self, latest_prices):
        """
        Updates position's latest price variable to help keep market value
        up to date.
        :latest_prices is a map of {symbol1: latest_price, symbol2: ...}
        """
        for pos in self.positions:
            pos.latest_price = latest_prices[pos.asset.symbol]

    def get_position(self, asset):
        for pos in self.positions:
            if pos.asset.id == asset.id:
                return pos
        return None

    @property
    def symbols(self):
        symbols = set()
        for pos in self.positions:
            symbols.add(pos.asset.symbol)
        return list(symbols)

    @property
    def weights(self):
        res = {'cash':0.0}
        if self.total_value == 0.0:
            return res
        for pos in self.positions:
            res[pos.asset.id] = pos.market_value / self.total_value
        res['cash'] = self.cash / self.total_value
        return res

    @property
    def positions_value(self):
        return self.perf.get_positions_value(self.positions)

    @property
    def total_value(self):
        return self.cash + self.positions_value

    def to_dict(self):
        return {
            'starting_cash': self.starting_cash,
            'cash': self.cash,
            'weights': self.weights,
            'pnl': self.perf.pnl,
            'returns': self.perf.returns,
            'total_value': self.total_value,
            'performance': self.perf.to_dict(),
            'positions': [pos.to_dict() for pos in self.positions]
        }

    @classmethod
    def from_dict(self, dct):
        dct = copy.deepcopy(dct)
        port = Portfolio(
            starting_cash=dct['starting_cash'],
            perf_tracker=PerformanceTracker.from_dict(dct['performance'])
        )
        positions = []
        for idx,pos in enumerate(dct['positions']):
            positions.append(Position.from_dict(pos))
        port.positions = positions
        port.cash = dct['cash']
        port.pnl = dct['pnl']
        port.returns = dct['returns']
        return port

    def to_json(self):
        return json.dumps(
            self.to_dict(),
            cls=EnumEncoder,
            indent=4)

    def __repr__(self):
        return self.to_json()
