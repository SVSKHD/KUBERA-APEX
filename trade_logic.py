import MetaTrader5 as mt5
from trade_management import order_send
from trade_logic_utils import scale_number, calculate_crypto_profit, calculate_currency_profit, print_open_positions, \
    check_and_close_trades, check_loss_and_close_trades, check_profit_and_close_trades
from risk_management import close_all_trades, close_position
import math

CANDLE_DATA = 20
pip_size = 0.0001
opposite_pip_move = 10  # Pip difference to check for the opposite market move
reference_price = None
last_trade = {"price": None, "direction": None}


def retrieve_market_data(symbol):
    """Retrieve and return market data for the symbol."""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
    high = max(rate['high'] for rate in rates)
    low = min(rate['low'] for rate in rates)
    current_price = mt5.symbol_info_tick(symbol).ask
    return high, low, current_price


def calculate_pip_differences(high, low, current_price):
    """Calculate and return pip differences from high and low."""
    high_diff = abs(high - current_price) / pip_size
    low_diff = abs(current_price - low) / pip_size
    return high_diff, low_diff


def make_trading_decision(symbol, high_diff, low_diff, current_price, pip_difference):
    global last_trade, reference_price
    # Initialize the reference price if it's None (i.e., when the bot is switched on)
    if reference_price is None:
        reference_price = current_price
        print(f"Reference price set at {reference_price} for {symbol}")

    # Check if the current price is 15 pips away from the reference price before making a decision
    if abs(reference_price - current_price) >= 15 * pip_size:
        if high_diff <= pip_difference and (last_trade["direction"] != 'SELL' or last_trade["price"] - current_price >= pip_difference * pip_size):
            print(f"TL.py : High price proximity alert for {symbol}. Possible SELL.")
            order_send(symbol, 'SELL', 0.01)
            last_trade = {"price": current_price, "direction": 'SELL'}
            reference_price = current_price  # Update the reference price after a trade
        elif low_diff <= pip_difference and (last_trade["direction"] != 'BUY' or current_price - last_trade["price"] >= pip_difference * pip_size):
            print(f"TL.py : Low price proximity alert for {symbol}. Possible BUY.")
            order_send(symbol, 'BUY', 0.01)
            last_trade = {"price": current_price, "direction": 'BUY'}
            reference_price = current_price  # Update the reference price after a trade
        else:
            print(f"TL.py : No trade triggered for {symbol}. Price stable within defined parameters.")
    else:
        print(f"No trade for {symbol} as price movement ({abs(reference_price - current_price):.5f}) has not reached 15 pips.")


def check_price_difference(symbol):
    """Function to check price differences for a given trading symbol."""
    pip_difference = 2000 if symbol == "BTCUSD" else 15  # BTC has larger price movements
    high, low, current_price = retrieve_market_data(symbol)
    high_diff = abs(high - current_price) / pip_size
    low_diff = abs(current_price - low) / pip_size
    print(f"TL.py : Live Price for {symbol}: {current_price}, High Diff: {high_diff}, Low Diff: {low_diff}")

    loss_percentage, profit_percentage, _, positions = print_open_positions()
    check_and_close_trades()
    check_loss_and_close_trades(loss_percentage)
    check_profit_and_close_trades(profit_percentage)

    make_trading_decision(symbol, high_diff, low_diff, current_price, pip_difference)
