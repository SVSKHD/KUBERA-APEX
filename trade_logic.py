import MetaTrader5 as mt5
from trade_management import order_send
from trade_logic_utils import (print_open_positions, check_and_close_trades,
                               check_loss_and_close_trades, check_profit_and_close_trades)
import math

CANDLE_DATA = 20
pip_size = 0.0001
reference_price = None
last_trade = {"price": None, "direction": None, "count": 0}


def retrieve_market_data(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
    high = max(rate['high'] for rate in rates)
    low = min(rate['low'] for rate in rates)
    current_price = mt5.symbol_info_tick(symbol).ask
    return high, low, current_price


def calculate_pip_differences(high, low, current_price):
    high_diff = abs(high - current_price) / pip_size
    low_diff = abs(current_price - low) / pip_size
    return high_diff, low_diff


def make_trading_decision(symbol, high_diff, low_diff, current_price, pip_difference):
    global last_trade, reference_price
    if last_trade["count"] >= 4:
        print(f"Maximum trade limit reached for {symbol}. No further trades will be executed.")
        return

    if last_trade["price"] is not None:
        last_pip_diff = abs(last_trade["price"] - current_price) / pip_size
    else:
        last_pip_diff = abs(reference_price - current_price) / pip_size if reference_price is not None else None

    if last_pip_diff is None or last_pip_diff >= 15:
        if high_diff >= pip_difference and last_trade["direction"] != 'SELL':
            print(f"High price proximity alert for {symbol}. Executing SELL.")
            order_send(symbol, 'SELL', 0.01)
            last_trade = {"price": current_price, "direction": 'SELL', "count": last_trade["count"] + 1}
        elif low_diff >= pip_difference and last_trade["direction"] != 'BUY':
            print(f"Low price proximity alert for {symbol}. Executing BUY.")
            order_send(symbol, 'BUY', 0.01)
            last_trade = {"price": current_price, "direction": 'BUY', "count": last_trade["count"] + 1}
        else:
            print("No trade executed. Market conditions not met.")
    else:
        print(f"No trade executed for {symbol}. Required pip difference not achieved (last diff: {last_pip_diff:.2f}).")


def check_price_difference(symbol):
    pip_difference = 2000 if symbol == "BTCUSD" else 15
    high, low, current_price = retrieve_market_data(symbol)
    high_diff, low_diff = calculate_pip_differences(high, low, current_price)
    print(f"Current Price: {current_price}, High Diff: {high_diff}, Low Diff: {low_diff} reference : {reference_price}")
    make_trading_decision(symbol, high_diff, low_diff, current_price, pip_difference)
    check_and_close_trades()
    check_loss_and_close_trades(1)  # Example percentage
    check_profit_and_close_trades(2)  # Example percentage

