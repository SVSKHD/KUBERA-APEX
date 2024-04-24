import MetaTrader5 as mt5
import time


def get_account_balance():
    """Retrieve and print the balance of the connected MT5 account."""
    if not mt5.terminal_info():
        print("Error: Not connected to MT5.")
        return

    account_info = mt5.account_info()
    if account_info is None:
        error_code, error_description = mt5.last_error()
        print(f"Error: Failed to get account info, error code = {error_code}, description = {error_description}")
    else:
        print(f"Account Balance: {account_info.balance}")


def connect_to_mt5(account_number, password, server):
    """Initialize MT5 connection and login to the specified account."""
    if not mt5.initialize():
        error_code, error_description = mt5.last_error()
        print(f"Error: initialize() failed, error code = {error_code}, description = {error_description}")
        return False

    if mt5.login(account_number, password=password, server=server):
        get_account_balance()
        print(f"Connected to MT5 account #{account_number}")
        return True
    else:
        error_code, error_description = mt5.last_error()
        print(f"Error: login() failed, error code = {error_code}, description = {error_description}")
        mt5.shutdown()
        return False


# ------------------------------------------------------------------------------- manage-orders


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


# ---------------------------------------------------------------------------------- main logic
def calculate_pips(price1, price2, symbol_info):
    return (price1 - price2) / symbol_info.point


def trading_logic(symbol, lot, pips_interval, opposite_direction_tolerance):
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} is not available, can not proceed.")
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, can not proceed.")
        return

    entry_price = mt5.symbol_info_tick(symbol).ask

    try:
        while True:
            current_price = mt5.symbol_info_tick(symbol).ask

            # Check if the current price has moved 15 pips from the last entry price
            if calculate_pips(current_price, entry_price, symbol_info) >= pips_interval:
                # Logic to place a trade, this function should be defined elsewhere
                # place_trade(symbol, lot, mt5.ORDER_TYPE_BUY, current_price)
                print(f"Placing trade at {current_price}")
                # Update the entry price for the next interval
                entry_price = current_price

            # If the market moves in the opposite direction, close all trades
            if calculate_pips(entry_price, current_price, symbol_info) >= opposite_direction_tolerance:
                close_all_trades()
                print("Closed all trades due to adverse price movement.")
                # Reset the entry price
                entry_price = current_price

            time.sleep(1)  # Control the frequency of the while loop

    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        mt5.shutdown()  # Disconnect from the MT5 terminal
