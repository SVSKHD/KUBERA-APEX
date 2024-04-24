import MetaTrader5 as mt5


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


# ------------------------------------------------------------------------------- close-all-orders


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
