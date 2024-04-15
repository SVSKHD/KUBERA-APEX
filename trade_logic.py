import MetaTrader5 as mt5
from trade_management import order_send
from risk_management import close_all_trades, close_position  # Assume close_position function is correctly implemented to close individual positions
import math

CANDLE_DATA = 50
pip_size = 0.0001
opposite_pip_move = 10  # Pip difference to check for the opposite market move

last_trade = {"price": None, "direction": None}

def scale_number(num):
    if num == 0:
        return 0
    scale_down_factor = 10 ** (int(math.log10(num)) - 3)
    return int(num / scale_down_factor)

def calculate_crypto_profit(position, current_price):
    return (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume

def calculate_currency_profit(position, current_price):
    return (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume * 100000

def print_open_positions():
    total_loss = 0
    account_info = mt5.account_info()
    initial_balance = account_info.balance
    positions = mt5.positions_get()
    if positions:
        for position in positions:
            current_price = mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask
            profit = calculate_crypto_profit(position, current_price) if 'BTC' in position.symbol else calculate_currency_profit(position, current_price)
            total_loss += profit
            print(f"Position ID: {position.ticket}, Symbol: {position.symbol}, Type: {'BUY' if position.type == 0 else 'SELL'}, Volume: {position.volume}, Open Price: {position.price_open}, Current Price: {current_price}, Profit: {profit:.2f} USD")
    else:
        print("No open positions currently.")
    loss_percentage = (total_loss / initial_balance) * 100
    print(f"Total running loss/gain: {total_loss:.2f} USD, which is {loss_percentage:.2f}% of the initial balance: {initial_balance:.2f}")
    return loss_percentage, positions

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

def check_and_close_trades():
    _, positions = print_open_positions()  # Retrieve the latest positions
    for position in positions:
        current_price = mt5.symbol_info_tick(position.symbol).ask if position.type == 0 else mt5.symbol_info_tick(position.symbol).bid
        price_diff = (current_price - position.price_open) / pip_size
        if (position.type == 0 and price_diff <= -opposite_pip_move) or \
           (position.type == 1 and price_diff >= opposite_pip_move):
            print(f"Closing Position ID {position.ticket} due to price movement against position by {opposite_pip_move} pips.")
            close_position(position.ticket)
        else:
            print(f"Position ID {position.ticket} remains open. Current Price Diff: {price_diff} pips.")

def check_loss_and_close_trades(loss_percentage):
    if loss_percentage <= -1:
        print(f"Closing all trades due to a loss exceeding 1% of the account balance.")
        close_all_trades()
        last_trade.update({"price": None, "direction": None})
