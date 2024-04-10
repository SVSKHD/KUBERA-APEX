# import MetaTrader5 as mt5
# from trade_management import order_send
# CANDLE_DATA = 30
# pip_size = 0.0001
# pip_difference = 15
#
# # Variable to track the last trade price
# last_trade_price = None
#
#
# def check_price_difference(symbol):
#     global last_trade_price
#
#     rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
#
#     high = rates[0]['high']
#     low = rates[0]['low']
#
#     # Iterate through the rates to find the actual highest and lowest
#     for rate in rates:
#         if rate['high'] > high:
#             high = rate['high']
#         if rate['low'] < low:
#             low = rate['low']
#
#     current_price = mt5.symbol_info_tick(symbol).ask
#
#     high_diff = abs(high - current_price) / pip_size
#     low_diff = abs(current_price - low) / pip_size
#
#     if high_diff <= pip_difference:
#         print(
#             f"The current price of {symbol} is within {pip_difference} pips of the highest price over the last {CANDLE_DATA} candles. Current Price: {current_price}, Highest: {high}")
#         if last_trade_price is None or abs(last_trade_price - current_price) >= pip_difference * pip_size:
#             order_send(symbol, 'SELL', 0.01)  # Replace with actual volume as required
#             last_trade_price = current_price
#     elif low_diff <= pip_difference:
#         print(
#             f"The current price of {symbol} is within {pip_difference} pips of the lowest price over the last {CANDLE_DATA} candles. Current Price: {current_price}, Lowest: {low}")
#         if last_trade_price is None or abs(last_trade_price - current_price) >= pip_difference * pip_size:
#             order_send(symbol, 'BUY', 0.01)  # Replace with actual volume as required
#             last_trade_price = current_price
#     else:
#         print(
#             f"No significant price difference observed for {symbol} over the last {CANDLE_DATA} candles. Current Price: {current_price}, Lowest: {low}, Highest: {high}")
#
#
#
import MetaTrader5 as mt5
from trade_management import order_send
from risk_management import close_all_trades

CANDLE_DATA = 30
pip_size = 0.0001
pip_difference = 15
opposite_pip_move = 10  # Pip difference to check for the opposite market move

# Variable to track the last trade price and its direction
last_trade = {"price": None, "direction": None}


def check_price_difference(symbol):
    global last_trade

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)
    high, low = rates[0]['high'], rates[0]['low']

    # Find the actual highest and lowest prices in the given data
    for rate in rates:
        if rate['high'] > high:
            high = rate['high']
        if rate['low'] < low:
            low = rate['low']

    current_price = mt5.symbol_info_tick(symbol).ask
    high_diff, low_diff = abs(high - current_price) / pip_size, abs(current_price - low) / pip_size

    # Function to handle trade opening and updating last trade details
    def handle_trade(direction, trade_price):
        order_send(symbol, direction, 0.01)  # Modify volume as required
        last_trade.update({"price": trade_price, "direction": direction})

    # Close all trades if the market moves 10 pips in the opposite direction
    if last_trade["price"] is not None:
        price_diff = (current_price - last_trade["price"]) / pip_size
        if (last_trade["direction"] == 'BUY' and price_diff <= -opposite_pip_move) or \
                (last_trade["direction"] == 'SELL' and price_diff >= opposite_pip_move):
            close_all_trades()
            last_trade.update({"price": None, "direction": None})  # Reset last trade details
            print(f"All positions closed due to a {opposite_pip_move} pip move against the last trade.")

    # Check for 15-pip interval and place trades accordingly
    if last_trade["price"] is None or abs(last_trade["price"] - current_price) >= pip_difference * pip_size:
        if high_diff <= pip_difference:
            print(
                f"Current price of {symbol} is close to the highest price over the last {CANDLE_DATA} candles. Considering to SELL.")
            handle_trade('SELL', current_price)
        elif low_diff <= pip_difference:
            print(
                f"Current price of {symbol} is close to the lowest price over the last {CANDLE_DATA} candles. Considering to BUY.")
            handle_trade('BUY', current_price)
        else:
            print(
                f"No significant price difference observed for {symbol} over the last {CANDLE_DATA} candles. Current Price: {current_price}, Lowest: {low}, Highest: {high}")
