import os
import tempfile
import time

import numpy as np
import pandas as pd
import talib
from logbook import Logger

from catalyst import run_algorithm
from catalyst.api import symbol, record, order_target_percent, get_open_orders
from catalyst.exchange.stats_utils import extract_transactions
# We give a name to the algorithm which Catalyst will use to persist its state.
# In this example, Catalyst will create the `.catalyst/data/live_algos`
# directory. If we stop and start the algorithm, Catalyst will resume its
# state using the files included in the folder.
from catalyst.utils.paths import ensure_directory

NAMESPACE = 'mean_reversion_simple'
log = Logger(NAMESPACE)


# To run an algorithm in Catalyst, you need two functions: initialize and
# handle_data.

def initialize(context):
    # This initialize function sets any data or variables that you'll use in
    # your algorithm.  For instance, you'll want to define the trading pair (or
    # trading pairs) you want to backtest.  You'll also want to define any
    # parameters or values you're going to use.

    # In our example, we're looking at Ripple in Btc.
    context.xrp_btc = symbol('trx_btc')
    context.base_price = None
    context.current_day = None

    context.RSI_OVERSOLD = 30
    context.RSI_OVERBOUGHT = 80
    context.CANDLE_SIZE = '15T'

    context.start_time = time.time()


def handle_data(context, data):
    # This handle_data function is where the real work is done.  Our data is
    # minute-level tick data, and each minute is called a frame.  This function
    # runs on each frame of the data.

    # We flag the first period of each day.
    # Since cryptocurrencies trade 24/7 the `before_trading_starts` handle
    # would only execute once. This method works with minute and daily
    # frequencies.
    today = data.current_dt.floor('1D')
    if today != context.current_day:
        context.traded_today = False
        context.current_day = today

    # We're computing the volume-weighted-average-price of the security
    # defined above, in the context.xrp_btc variable.  For this example, we're
    # using three bars on the 15 min bars.

    # The frequency attribute determine the bar size. We use this convention
    # for the frequency alias:
    # http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases
    prices = data.history(
        context.xrp_btc,
        fields='close',
        bar_count=50,
        frequency=context.CANDLE_SIZE
    )

    # Ta-lib calculates various technical indicator based on price and
    # volume arrays.

    # In this example, we are comp
    rsi = talib.RSI(prices.values, timeperiod=14)

    # We need a variable for the current price of the security to compare to
    # the average. Since we are requesting two fields, data.current()
    # returns a DataFrame with
    current = data.current(context.xrp_btc, fields=['close', 'volume'])
    price = current['close']

    # If base_price is not set, we use the current value. This is the
    # price at the first bar which we reference to calculate price_change.
    if context.base_price is None:
        context.base_price = price

    price_change = (price - context.base_price) / context.base_price
    cash = context.portfolio.cash

    # Now that we've collected all current data for this frame, we use
    # the record() method to save it. This data will be available as
    # a parameter of the analyze() function for further analysis.
    record(
        price=price,
        volume=current['volume'],
        price_change=price_change,
        rsi=rsi[-1],
        cash=cash
    )

    # We are trying to avoid over-trading by limiting our trades to
    # one per day.
    if context.traded_today:
        return

    # Since we are using limit orders, some orders may not execute immediately
    # we wait until all orders are executed before considering more trades.
    orders = get_open_orders(context.xrp_btc)
    if len(orders) > 0:
        return

    # Exit if we cannot trade
    if not data.can_trade(context.xrp_btc):
        return

    # Another powerful built-in feature of the Catalyst backtester is the
    # portfolio object.  The portfolio object tracks your positions, cash,
    # cost basis of specific holdings, and more.  In this line, we calculate
    # how long or short our position is at this minute.
    pos_amount = context.portfolio.positions[context.xrp_btc].amount

    if rsi[-1] <= context.RSI_OVERSOLD and pos_amount == 0:
        log.info(
            '{}: buying - price: {}, rsi: {}'.format(
                data.current_dt, price, rsi[-1]
            )
        )
        # Set a style for limit orders,
        limit_price = price * 1.005
        order_target_percent(
            context.xrp_btc, 1, limit_price=limit_price
        )
        context.traded_today = True

    elif rsi[-1] >= context.RSI_OVERBOUGHT and pos_amount > 0:
        log.info(
            '{}: selling - price: {}, rsi: {}'.format(
                data.current_dt, price, rsi[-1]
            )
        )
        limit_price = price * 0.995
        order_target_percent(
            context.xrp_btc, 0, limit_price=limit_price
        )
        context.traded_today = True


def analyze(context=None, perf=None):
    end = time.time()
    log.info('elapsed time: {}'.format(end - context.start_time))

    import matplotlib.pyplot as plt
    # The base currency of the algo exchange
    base_currency = context.exchanges.values()[0].base_currency.upper()

    # Plot the portfolio value over time.
    ax1 = plt.subplot(611)
    perf.loc[:, 'portfolio_value'].plot(ax=ax1)
    ax1.set_ylabel('Portfolio\nValue\n({})'.format(base_currency))

    # Plot the price increase or decrease over time.
    ax2 = plt.subplot(612, sharex=ax1)
    perf.loc[:, 'price'].plot(ax=ax2, label='Price')

    ax2.set_ylabel('{asset}\n({base})'.format(
        asset=context.xrp_btc.symbol, base=base_currency
    ))

    transaction_df = extract_transactions(perf)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df['amount'] > 0]
        sell_df = transaction_df[transaction_df['amount'] < 0]
        ax2.scatter(
            buy_df.index.to_pydatetime(),
            perf.loc[buy_df.index.floor('1 min'), 'price'],
            marker='^',
            s=100,
            c='green',
            label=''
        )
        ax2.scatter(
            sell_df.index.to_pydatetime(),
            perf.loc[sell_df.index.floor('1 min'), 'price'],
            marker='v',
            s=100,
            c='red',
            label=''
        )

    ax4 = plt.subplot(613, sharex=ax1)
    perf.loc[:, 'cash'].plot(
        ax=ax4, label='Base Currency ({})'.format(base_currency)
    )
    ax4.set_ylabel('Cash\n({})'.format(base_currency))

    perf['algorithm'] = perf.loc[:, 'algorithm_period_return']

    ax5 = plt.subplot(614, sharex=ax1)
    perf.loc[:, ['algorithm', 'price_change']].plot(ax=ax5)
    ax5.set_ylabel('Percent\nChange')

    ax6 = plt.subplot(615, sharex=ax1)
    perf.loc[:, 'rsi'].plot(ax=ax6, label='RSI')
    ax6.set_ylabel('RSI')
    ax6.axhline(context.RSI_OVERBOUGHT, color='darkgoldenrod')
    ax6.axhline(context.RSI_OVERSOLD, color='darkgoldenrod')

    if not transaction_df.empty:
        ax6.scatter(
            buy_df.index.to_pydatetime(),
            perf.loc[buy_df.index.floor('1 min'), 'rsi'],
            marker='^',
            s=100,
            c='green',
            label=''
        )
        ax6.scatter(
            sell_df.index.to_pydatetime(),
            perf.loc[sell_df.index.floor('1 min'), 'rsi'],
            marker='v',
            s=100,
            c='red',
            label=''
        )
    plt.legend(loc=3)
    start, end = ax6.get_ylim()
    ax6.yaxis.set_ticks(np.arange(0, end, end/5))

    # Show the plot.
    plt.gcf().set_size_inches(18, 8)
    plt.show()
    pass


if __name__ == '__main__':
    # The execution mode: backtest or live
    MODE = 'live'

    if MODE == 'backtest':
        folder = os.path.join(
            tempfile.gettempdir(), 'catalyst', NAMESPACE
        )
        ensure_directory(folder)

        timestr = time.strftime('%Y%m%d-%H%M%S')
        out = os.path.join(folder, '{}.p'.format(timestr))
        # catalyst run -f catalyst/examples/mean_reversion_simple.py -x bitfinex -s 2017-10-1 -e 2017-11-10 -c usdt -n mean-reversion --data-frequency minute --capital-base 10000
        run_algorithm(
            capital_base=10000,
            data_frequency='minute',
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name='binance',
            algo_namespace=NAMESPACE,
            base_currency='usd',
            start=pd.to_datetime('2017-10-01', utc=True),
            end=pd.to_datetime('2017-11-10', utc=True),
            output=out
        )
        log.info('saved perf stats: {}'.format(out))

    elif MODE == 'live':
        run_algorithm(
            capital_base=0.03,
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name='binance',
            live=True,
            algo_namespace=NAMESPACE,
            base_currency='btc',
            live_graph=False,
            simulate_orders=True,
        )