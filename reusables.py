import MetaTrader5 as mt5
import time


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


# buy or close orders
def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price  # Current market price for buy order
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price  # Current market price for sell order

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to find symbol {symbol}, order_send() failed.")
        mt5.shutdown()
        return None

    point = symbol_info.point
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print(f"Invalid order type: {order_type}")
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
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_FOK,  # Immediate or cancel
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
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
def observe_price(symbol, pip_diff=15, volume=0.01):
    initial_price = get_live_price(symbol)
    if initial_price is None:
        mt5.shutdown()
        return

    print(f"Initial price for {symbol}: {initial_price}")

    try:
        while True:
            current_price = get_live_price(symbol)
            if current_price is None:
                continue

            pip_scale = 0.0001 if not symbol.endswith("JPY") else 0.01

            difference = (current_price - initial_price) / pip_scale
            if abs(difference) >= pip_diff:
                direction = "increased" if difference > 0 else "decreased"
                print(f"15 pip {direction} reached for {symbol}: {current_price} ({difference:+.2f} pips)")

                # Determine the order type based on direction of price movement
                order_type = 'BUY' if direction == "increased" else 'SELL'
                # Send the order
                order_send(symbol, order_type, volume)
                break

            time.sleep(1)

    finally:
        mt5.shutdown()


# Manage trades based on signals
def manage_trades(symbol, signal, max_trades=4, minimal_profit=0.0001):
    if not connect_to_mt5(123456, 'password', 'MetaQuotes-Demo'):  # Use your actual login credentials
        return

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


