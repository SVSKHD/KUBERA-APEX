import MetaTrader5 as mt5
from trade_management import order_send
from trade_logic_utils import scale_number, calculate_crypto_profit, calculate_currency_profit, print_open_positions, check_and_close_trades, check_loss_and_close_trades
from risk_management import close_all_trades, close_position  # Assume close_position function is correctly implemented to close individual positions
import math

CANDLE_DATA = 50
pip_size = 0.0001
opposite_pip_move = 10  # Pip difference to check for the opposite market move

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
    """Make trading decision based on the price differences and update last trade."""
    global last_trade
    if high_diff <= pip_difference:
        print(f"High price proximity alert for {symbol}. Possible SELL.")
        order_send(symbol, 'SELL', 0.01)
        last_trade = {"price": current_price, "direction": 'SELL'}
    elif low_diff <= pip_difference:
        print(f"Low price proximity alert for {symbol}. Possible BUY.")
        order_send(symbol, 'BUY', 0.01)
        last_trade = {"price": current_price, "direction": 'BUY'}
    else:
        print(f"No trade triggered for {symbol}. Price stable within defined parameters.")

def check_price_difference(symbol):
    """Function to check price differences for a given trading symbol."""
    pip_difference = 2000 if symbol == "BTCUSD" else 15
    high, low, current_price = retrieve_market_data(symbol)
    high_diff, low_diff = calculate_pip_differences(high, low, current_price)
    print(f"Live Price for {symbol}: {current_price}, High Diff: {high_diff}, Low Diff: {low_diff}")

    loss_percentage, _ = print_open_positions()
    check_and_close_trades()
    check_loss_and_close_trades(loss_percentage)

    if last_trade["price"] is None or abs(last_trade["price"] - current_price) >= pip_difference * pip_size:
        make_trading_decision(symbol, high_diff, low_diff, current_price, pip_difference)
