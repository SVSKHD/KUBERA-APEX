import MetaTrader5 as mt5
import time

# Import additional necessary modules
from datetime import datetime

# Reuse the existing functions here by either copying them directly or importing from another module if they are separated
# Assuming the functions are imported from a module named trading_functions
from trading_functions import connect_to_mt5, get_account_balance, order_send, close_all_trades, observe_price

def main():
    account_number = 123456  # your MetaTrader account number
    password = "your_password"  # your MetaTrader password
    server = "MetaQuotes-Demo"  # your MetaTrader server

    # Connect to MT5
    if not connect_to_mt5(account_number, password, server):
        print("Failed to connect to MT5, exiting.")
        return

    symbol = "EURUSD"  # Symbol to be observed
    pip_diff = 15  # Pip difference to trigger trade action
    volume = 0.01  # Volume of the trade

    # Main loop to observe the price at a 1-hour interval
    try:
        while True:
            current_time = datetime.now()
            print(f"Observing market at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Observe price movement and potentially execute trades
            observe_price(symbol, pip_diff, volume)

            # Wait for one hour before next check
            print("Waiting for the next hour check...")
            time.sleep(3600)  # Sleep time is in seconds (3600 seconds = 1 hour)

    except KeyboardInterrupt:
        print("Shutdown requested by user")
    except Exception as e:
        print("Error occurred:", str(e))
    finally:
        # Ensure MT5 is properly shut down
        if mt5.terminal_info() is not None:
            mt5.shutdown()

if __name__ == "__main__":
    main()
