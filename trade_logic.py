import MetaTrader5 as mt5
from trade_management import order_send
from trade_logic_utils import scale_number, calculate_crypto_profit, calculate_currency_profit, print_open_positions, check_and_close_trades, check_loss_and_close_trades
from risk_management import close_all_trades, close_position  # Assume close_position function is correctly implemented to close individual positions
import math

CANDLE_DATA = 50
pip_size = 0.0001
opposite_pip_move = 10  # Pip difference to check for the opposite market move

last_trade = {"price": None, "direction": None}

def check_price_difference(symbol):
    global last_trade
    pip_difference = 2000 if symbol == "BTCUSD" else 15
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
    high, low = max(rate['high'] for rate in rates), min(rate['low'] for rate in rates)
    current_price = mt5.symbol_info_tick(symbol).ask
    high_diff, low_diff = abs(high - current_price) / pip_size, abs(current_price - low) / pip_size
    print(f"Live Price for {symbol}: {current_price}, High Diff: {high_diff}, Low Diff: {low_diff}")

    # Unpack the values properly here
    loss_percentage, _ = print_open_positions()

    check_and_close_trades()
    check_loss_and_close_trades(loss_percentage)

    if last_trade["price"] is None or abs(last_trade["price"] - current_price) >= pip_difference * pip_size:
        if high_diff <= pip_difference:
            print(f"High price proximity alert for {symbol}. Possible SELL.")
            order_send(symbol, 'SELL', 0.01)
            last_trade = {"price": current_price, "direction": 'SELL'}
            print(f"Updated last_trade: {last_trade}")
        elif low_diff <= pip_difference:
            print(f"Low price proximity alert for {symbol}. Possible BUY.")
            order_send(symbol, 'BUY', 0.01)
            last_trade = {"price": current_price, "direction": 'BUY'}
            print(f"Updated last_trade: {last_trade}")
        else:
            print(f"No trade triggered for {symbol}. Price stable within defined parameters.")