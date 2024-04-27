import MetaTrader5 as mt5
import time
from datetime import datetime
import threading
import math

# Connection and Account Management ------------------------------------------------------------------------------------>

def connect_to_mt5(account_number, password, server):
    if not mt5.initialize():
        print("Initialize failed, error code =", mt5.last_error())
        return False

    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("Login failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    print(f"Connected to MT5 account #{account_number}")
    return True

def get_account_balance():
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info, error code =", mt5.last_error())
    else:
        print("Account Balance: ", account_info.balance)

# Trading Operations --------------------------------------------------------------------------------------------------->

def order_send(symbol, order_type, volume):
    price = mt5.symbol_info_tick(symbol).ask if order_type == 'BUY' else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
        "price": price,
        "slippage": 2,
        "magic": 0,
        "comment": "Automated trade",
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed, retcode={result.retcode}")
    else:
        print(f"Order successful, ticket={result.order}")

def close_all_trades():
    positions = mt5.positions_get()
    if not positions:
        print("No open positions.")
        return

    for position in positions:
        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": position.ticket,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
            "slippage": 2,
            "magic": 0,
            "comment": "Closing position",
            "type_filling": mt5.ORDER_FILLING_FOK,
        })
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Position {position.ticket} closed")
        else:
            print(f"Failed to close position {position.ticket}")

# Main Trading Logic --------------------------------------------------------------------------------------------------->

def start_trading(symbol, pip_diff, volume):
    print(f"Trading {symbol} with a pip difference of {pip_diff}")
    last_price = mt5.symbol_info_tick(symbol).ask

    while True:
        current_price = mt5.symbol_info_tick(symbol).ask
        if abs(current_price - last_price) >= pip_diff * (0.01 if 'JPY' in symbol else 0.0001):
            order_send(symbol, 'BUY' if current_price > last_price else 'SELL', volume)
            last_price = current_price  # Update the last trade price

        time.sleep(1)  # Delay to reduce CPU load

def main():
    account_number = 212792645
    password = 'pn^eNL4U'
    server = 'OctaFX-Demo'

    if not connect_to_mt5(account_number, password, server):
        print("Failed to connect to MT5, exiting.")
        return

    get_account_balance()

    threads = []
    for symbol in ['EURUSD', 'GBPUSD', 'USDJPY']:
        t = threading.Thread(target=start_trading, args=(symbol, 15, 0.1))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
