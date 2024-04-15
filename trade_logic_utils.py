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