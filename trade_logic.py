import MetaTrader5 as mt5
from trade_management import order_send
from risk_management import close_all_trades
import math

CANDLE_DATA = 50
pip_size = 0.0001
opposite_pip_move = 10  # Pip difference to check for the opposite market move

# Variable to track the last trade price and its direction
last_trade = {"price": None, "direction": None}


def scale_number(num):
    if num == 0:
        return 0
    scale_down_factor = 10 ** (int(math.log10(num)) - 3)  # Adjust '3' to get the first 4 significant figures
    return int(num / scale_down_factor)


def calculate_crypto_profit(position, current_price):
    # For cryptocurrencies like Bitcoin
    profit = (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume
    return profit


def calculate_currency_profit(position, current_price):
    # For non-crypto currencies
    profit = (current_price - position.price_open) * (1 if position.type == 0 else -1) * position.volume * 100000
    return profit


def print_open_positions():
    total_loss = 0
    account_info = mt5.account_info()
    initial_balance = account_info.balance
    positions = mt5.positions_get()
    if positions:
        for position in positions:
            current_price = mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(
                position.symbol).ask
            if 'BTC' in position.symbol:
                profit = calculate_crypto_profit(position, current_price)
            else:
                profit = calculate_currency_profit(position, current_price)
            total_loss += profit
            print(f"Position ID: {position.ticket}, Symbol: {position.symbol}, Type: {'BUY' if position.type == 0 else 'SELL'}, Volume: {position.volume}, Open Price: {position.price_open}, Current Price: {current_price}, Profit: {profit:.2f} USD")
    else:
        print("No open positions currently.")

    loss_percentage = (total_loss / initial_balance) * 100
    print(f"Total running loss/gain: {total_loss:.2f} USD, which is {loss_percentage:.2f}% of the initial balance: {initial_balance:.2f}")
    return loss_percentage

def check_price_difference(symbol):
    global last_trade
    pip_difference = 2000 if symbol == "BTCUSD" else 15

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
    high, low = rates[0]['high'], rates[0]['low']
    for rate in rates:
        if rate['high'] > high:
            high = rate['high']
        if rate['low'] < low:
            low = rate['low']

    current_price = mt5.symbol_info_tick(symbol).ask
    print(f"Live Price for {symbol}: {current_price}")
    high_diff, low_diff = abs(high - current_price) / pip_size, abs(current_price - low) / pip_size

    def handle_trade(direction, trade_price):
        order_send(symbol, direction, 0.01)  # Modify volume as required
        last_trade.update({"price": trade_price, "direction": direction})
        print(f"Trade placed: {direction} at {trade_price}")

    loss_percentage = print_open_positions()
    check_and_close_trades(current_price)
    check_loss_and_close_trades(loss_percentage)

    if last_trade["price"] is None or abs(last_trade["price"] - current_price) >= pip_difference * pip_size:
        if high_diff <= pip_difference:
            print(f"Current price of {symbol} is close to the highest price over the last {CANDLE_DATA} candles. Considering to SELL.")
            handle_trade('SELL', current_price)
        elif low_diff <= pip_difference:
            print(f"Current price of {symbol} is close to the lowest price over the last {CANDLE_DATA} candles. Considering to BUY.")
            handle_trade('BUY', current_price)
        else:
            print(f"No significant price difference observed for {symbol} over the last {CANDLE_DATA} candles. Current Price: {current_price}, Lowest: {low}, Highest: {high}, pip-difference low - {low_diff}, high-diff - {high_diff}")

# These functions are called to check and close trades based on specific conditions
def check_and_close_trades(current_price):
    global last_trade
    if last_trade["price"] is not None:
        price_diff = (current_price - last_trade["price"]) / pip_size
        if (last_trade["direction"] == 'BUY' and price_diff <= -opposite_pip_move) or \
           (last_trade["direction"] == 'SELL' and price_diff >= opposite_pip_move):
            close_all_trades()
            last_trade.update({"price": None, "direction": None})
            print(f"All positions closed due to a {opposite_pip_move} pip move against the last trade.")

def check_loss_and_close_trades(loss_percentage):
    if loss_percentage <= -1:
        close_all_trades()
        last_trade.update({"price": None, "direction": None})
        print(f"All positions closed due to a total loss exceeding 1%.")
