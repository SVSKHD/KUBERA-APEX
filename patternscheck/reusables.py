import MetaTrader5 as mt5
import time
import math

# start the connection between meta trader5 and app
def connect_to_mt5(account_number, password, server):
    # Initialize MT5 connection
    if not mt5.initialize():
        print("S.py : initialize() failed, error code =", mt5.last_error())
        return False

    # Connect to the trading account
    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("S.py : login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    print("reusables.py : Connected to MT5 account #{}".format(account_number))
    return True


# get account balance of logged in account creds
def get_account_balance():
    if mt5.terminal_info() is None:
        print("S.py : Not connected to MT5.")
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("S.py : Failed to get account info, error code =", mt5.last_error())
    else:
        print("S.py :  Account Balance: ", account_info.balance)


def adjust_volume(volume, symbol_info):
    min_volume = symbol_info.volume_min
    step = symbol_info.volume_step
    volume = max(min_volume, volume)  # Ensure volume is at least the minimum
    # Adjust volume to the nearest step multiple above the minimum
    volume = ((int((volume - min_volume) / step) + 1) * step) + min_volume if volume % step != 0 else volume
    return volume

def adjust_price(price, symbol_info):
    point = symbol_info.point
    price_scale = round(-math.log10(point))
    return round(price, price_scale)

# Trade Methods ---------------------------------------------------------------------------------------------------------------------------------Section>


def is_hammer(candle):
    """
    Determine if a candlestick is a hammer.

    Args:
        candle (dict): A dictionary containing open, high, low, and close prices of a candle.

    Returns:
        bool: True if the candle is a hammer, False otherwise.
    """
    # Define the criteria for a hammer
    body = abs(candle['close'] - candle['open'])
    candle_range = candle['high'] - candle['low']
    lower_wick = min(candle['close'], candle['open']) - candle['low']
    upper_wick = candle['high'] - max(candle['close'], candle['open'])

    # Hammer: small body, long lower wick, very small or no upper wick
    return body <= candle_range * 0.3 and lower_wick >= body * 2 and upper_wick <= body * 0.5


def determine_market_trend(symbol):
    """
    Determine the market trend by identifying the presence of a hammer candlestick pattern.

    Args:
        symbol (str): The trading symbol (e.g., 'EURUSD').

    Returns:
        str: 'BULLISH' if a hammer pattern is found, 'BEARISH' otherwise.
    """
    # Ensure the symbol is available
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol {symbol} not available")
        return 'INDETERMINATE'

    # Define the timeframe
    timeframe = mt5.TIMEFRAME_H1

    # Retrieve the latest candle
    candles = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)

    if candles is None:
        print("Failed to retrieve candles")
        return 'INDETERMINATE'

    # Check if the latest candle is a hammer
    if is_hammer(candles[0]):
        return 'BULLISH'
    else:
        return 'BEARISH'


# buy or close orders
def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Failed to find symbol, order send failed.")
        return None

    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print("Invalid order type.")
        return None


    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "slippage": slippage,
        "magic": magic,
        "comment": comment,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={result.retcode}")
    else:
        print(f"Order sent successfully, ticket={result.order}")

    return result







def close_all_trades():
    # Retrieve information about all open positions
    positions = mt5.positions_get()
    if positions is None:
        print("No positions found, error code =", mt5.last_error())
    elif len(positions) > 0:
        for position in positions:
            symbol = position.symbol
            volume = position.volume
            position_id = position.ticket
            trade_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            # Prepare the request for closing the position
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "position": position_id,
                "magic": 0,
                "comment": "Closed by script",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Send the trade request
            result = mt5.order_send(close_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to close position {position_id}: {result}")
            else:
                print(f"reusabale.py : Position {position_id} closed successfully.")


# Price Handling ---------------------------------------------------------------------------------------------------------------------------------Section>
# Get the live price of a currency pair
def get_live_price(symbol):
    # Check if the symbol exists in MT5
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} not found, can't get price.")
        return None

    # Get tick data
    tick = mt5.symbol_info_tick(symbol)
    return tick.ask  # You can change to tick.bid based on your requirement


# Observe price and check for 15 pip difference


def observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10):
    # Ensure the symbol is available in MT5
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}, symbol not found on MT5.")
        mt5.shutdown()
        return

    # Get the initial tick data for real-time analysis
    initial_tick = mt5.symbol_info_tick(symbol)
    if initial_tick is None:
        print("Failed to get tick data for", symbol)
        mt5.shutdown()
        return
    last_traded_price = initial_tick.ask  # Start with the current ask price

    print(f"Starting observation for {symbol} at price: {last_traded_price}")

    order_type=None

    try:
        while True:
            current_tick = mt5.symbol_info_tick(symbol)
            if current_tick is None:
                continue  # Skip this iteration if tick data is not available

            current_price = current_tick.ask
            pip_scale = 0.0001 if not symbol.endswith("JPY") else 0.01
            difference = (current_price - last_traded_price) / pip_scale

            # Check if the price has moved 15 pips away from the last traded price
            if abs(difference) >= pip_diff:
                direction = "increased" if difference > 0 else "decreased"
                print(
                    f"{pip_diff} pip {direction} reached for {symbol} at price: {current_price} ({difference:+.2f} pips)")
                close_all_trades()
                order_type = 'BUY' if direction == "increased" else 'SELL'
                order_send(symbol, order_type, volume)  # Execute the trade
                last_traded_price = current_price  # Update the last traded price to current
                print(f"New base price for next trade: {last_traded_price}")

            # Monitoring for stop loss condition
            loss_difference = (current_price - last_traded_price) / pip_scale
            if (order_type == 'BUY' and loss_difference <= -stop_loss_pips) or (
                    order_type == 'SELL' and loss_difference >= stop_loss_pips):
                print(f"Market moved {stop_loss_pips} pips against the position; closing all trades.")
                close_all_trades()  # Close all trades if the market moves 10 pips against the trade
                break  # Optional: stop the function after closing trades to reassess strategy

            time.sleep(1)  # Small delay to prevent excessive CPU usage
    finally:
        mt5.shutdown()


# Manage trades based on signals
def manage_trades(symbol, signal, max_trades=4, minimal_profit=0.0001):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None and mt5.last_error()[0] != 1:  # No positions error code
            print("Failed to get positions for", symbol)
            return

        current_trades = len(positions)
        if positions and (signal == 'buy' and positions[0].type == mt5.ORDER_TYPE_SELL) or \
                (signal == 'sell' and positions[0].type == mt5.ORDER_TYPE_BUY):
            for pos in positions:
                close_position(pos, minimal_profit)

        if current_trades < max_trades:
            order_send(symbol, signal.upper(), 0.01)  # Example: 0.01 lots

    finally:
        mt5.shutdown()


# Close position with minimal profit check
def close_position(position, minimal_profit):
    current_price = mt5.symbol_info_tick(
        position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
    if (position.type == mt5.ORDER_TYPE_BUY and (current_price - position.price) > minimal_profit) or \
            (position.type == mt5.ORDER_TYPE_SELL and (position.price - current_price) > minimal_profit):
        order_send(position.symbol, 'SELL' if position.type == mt5.ORDER_TYPE_BUY else 'BUY', position.volume,
                   current_price)


