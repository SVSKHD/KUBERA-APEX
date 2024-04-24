import threading
from refinedReusables import connect_to_mt5, trading_logic

# Your account details
account_number = 212792645  # Your account number
password = 'pn^eNL4U'  # Your password
server = 'OctaFX-Demo'  # Your server

# The symbol(s) you want to trade, and their respective settings
trading_symbols = [
    {'symbol': 'EURUSD', 'lot': 0.1, 'pips_interval': 15, 'opposite_direction_tolerance': 10},
    # Add more symbols if necessary
    {'symbol': 'GBPUSD', 'lot': 0.1, 'pips_interval': 15, 'opposite_direction_tolerance': 10},
]


def run_trading_strategy():
    # Connect to MT5
    if connect_to_mt5(account_number, password, server):
        threads = []
        for symbol_settings in trading_symbols:
            t = threading.Thread(target=trading_logic, kwargs=symbol_settings)
            threads.append(t)
            t.start()

        # Join threads to ensure they all complete before exiting
        for thread in threads:
            thread.join()


if __name__ == "__main__":
    try:
        run_trading_strategy()
    except Exception as e:
        print(f"An error occurred in main.py: {e}")
    finally:
        print("Trading strategy has been stopped.")
