import MetaTrader5 as mt5
import math


def scale_number(num):
    if num == 0:
        return 0
    scale_down_factor = 10 ** (int(math.log10(num)) - 3)
    return int(num / scale_down_factor)

def calculate_crypto_profit(position, current_price):
    return (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume

def calculate_currency_profit(position, current_price):
    return (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume * 100000

def fetch_positions():
    try:
        positions = mt5.positions_get()
        for position in positions:
            yield position
    except Exception as e:
        print(f"Failed to fetch positions: {e}")
        return []

def print_open_positions():
    """Prints all open positions and calculates the total loss percentage."""
    total_loss = 0
    count = 0
    for position in fetch_positions():
        print(f"Position ID: {position.ticket}, Profit: {position.profit}")
        total_loss += position.profit  # Assuming profit can be negative for a loss
        count += 1
    loss_percentage = (total_loss / count) * 100 if count > 0 else 0
    print(f"Total Loss Percentage: {loss_percentage}%")
    return loss_percentage, count


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