import time
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_bars, shutdown_mt5

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'

def main():
    # Initialize connection to MetaTrader 5
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        # Symbol to monitor and trade
        symbol = "EURUSD"

        # Start observing the market
        try:
            while True:
                # Fetch the latest bars data from MT5
                bars = fetch_bars(symbol, mt5.TIMEFRAME_H1, 100)  # Fetching 100 bars for the 1-hour timeframe

                if bars:
                    # Analyze and trade based on the fetched bars
                    analyze_and_trade(symbol, bars)
                else:
                    print("Failed to fetch bars for analysis.")

                # Observe price for specific changes
                observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10)

                # Sleep to avoid hitting rate limits or overloading CPU
                time.sleep(1)  # Check every minute

        except KeyboardInterrupt:
            print("Shutting down the trading script.")
        finally:
            # Properly shutdown MT5 connection
            shutdown_mt5()  # Ensure this function exists to properly close the MT5 connection

def shutdown_mt5():
    print("Closing MT5 connection.")
    mt5.shutdown()

if __name__ == "__main__":
    main()
