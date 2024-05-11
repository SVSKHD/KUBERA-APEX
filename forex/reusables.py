# reusables.py
import MetaTrader5 as mt5
import pandas as pd

balance = None


def connect_to_mt5(account_number, password, server):
    if not mt5.initialize():
        print("reusables.py : initialize() failed, error code =", mt5.last_error())
        return False
    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("reusables.py : login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False
    print("reusables.py : Connected to MT5 account #{}".format(account_number))
    return True


def get_account_balance():
    account_info = mt5.account_info()
    if account_info is None:
        print("reusables.py : Failed to get account info, error code =", mt5.last_error())
    else:
        print("reusables.py : Account Balance: ", account_info.balance)
        return account_info.balance


def get_open_orders(open_params=None):
    open_orders = mt5.orders_get(**open_params) if open_params else mt5.orders_get()
    if open_orders is None:
        print("reusables.py: No opened orders or failed to retrieve orders, error code =", mt5.last_error())
    else:
        df = pd.DataFrame(list(open_orders), columns=open_orders[0]._asdict().keys())
        print(df)


# order management------------------------
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


# profit and loss trades calculations------
def check_positions_and_close(balance):
    positions = mt5.positions_get()
    if positions is None:
        print("reusables.py: No open positions to check.")
        return

    total_profit = sum(pos.profit for pos in positions)
    profit_threshold = 0.02 * balance
    loss_threshold = -0.01 * balance

    if total_profit >= profit_threshold or total_profit <= loss_threshold:
        print(f"reusables.py: Closing all positions due to threshold breach. Total Profit/Loss: {total_profit}")
        close_all_trades()


def mainExecutor(account_number, password, server):
    if connect_to_mt5(account_number, password, server):
        balance = get_account_balance()  # Retrieve and store account balance
        if balance is not None:  # Check if account balance was successfully retrieved
            check_positions_and_close(balance)
    mt5.shutdown()

