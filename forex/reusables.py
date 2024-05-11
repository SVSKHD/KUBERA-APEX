import MetaTrader5 as mt5
import time
import math
import pandas as pd


# connect to mt5
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


def get_account_balance():
    if mt5.terminal_info() is None:
        print("S.py : Not connected to MT5.")
        return
    account_info = mt5.account_info()
    if account_info is None:
        print("S.py : Failed to get account info, error code =", mt5.last_error())
    else:
        print("S.py :  Account Balance: ", account_info.balance)


# Get currently opened orders
def get_open_orders(account_number, password, server):
    if not connect_to_mt5(account_number, password, server):
        return
    open_orders = mt5.orders_get()
    if open_orders is None:
        print("S.py: No opened orders or failed to retrieve orders, error code =", mt5.last_error())
    else:
        df = pd.DataFrame(list(open_orders), columns=open_orders[0]._asdict().keys())
        print(df)