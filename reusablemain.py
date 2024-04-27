import MetaTrader5 as mt5
import time
from datetime import datetime
import threading
from reusables import connect_to_mt5, get_account_balance, observe_price, manage_trades

def start_trading(symbol, pip_diff, volume, max_trades, minimal_profit):
    try:
        while True:
            current_time = datetime.now()
            print(f"{symbol}: Observing market at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Observe price movements and potentially execute trades
            observe_price(symbol, pip_diff, volume, stop_loss_pips=10000)

            # Manage existing trades based on current market conditions
            manage_trades(symbol, 'buy', max_trades, minimal_profit)

            print(f"{symbol}: Waiting for the next hour check...")
            time.sleep(1)  # Sleep for 1 hour

    except Exception as e:
        print(f"Error with {symbol}: {str(e)}")

def main():
    account_number = 212792645
    password = 'pn^eNL4U'
    server = 'OctaFX-Demo'

    if not connect_to_mt5(account_number, password, server):
        print("Failed to connect to MT5, exiting.")
        return

    get_account_balance()

    volume = 0.1
    max_trades = 4
    minimal_profit = 10

    # Define symbols and settings based on the day of the week
    weekday_symbols = {'EURUSD': 10, 'GBPUSD': 10}
    weekend_symbols = {'BTCUSD': 25000, 'ETHUSD': 25000}

    # Determine the current day and choose the symbol set
    current_day = datetime.now().weekday()  # Monday is 0 and Sunday is 6
    symbols = weekend_symbols if current_day in [5, 6] else weekday_symbols

    # Create threads for each symbol
    threads = []
    for symbol, pip_diff in symbols.items():
        t = threading.Thread(target=start_trading, args=(symbol, pip_diff, volume, max_trades, minimal_profit))
        threads.append(t)
        t.start()

    # Wait for all threads to complete (which they never will under normal conditions)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
