import MetaTrader5 as mt5
import time
import datetime
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_bars, daily_trading_recommendations

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'

def main():
    # Initialize connection to MetaTrader 5
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        # Run the trading based on the day of the week
        recommendation = daily_trading_recommendations()
        print(recommendation)

        # Determine the symbol and adjust volumes based on day and balance
        today = datetime.datetime.now()
        is_weekend = today.weekday() in [5, 6]  # 5 is Saturday, 6 is Sunday
        if is_weekend:
            symbol = "BTCUSD"
            balance = 10000  # Example balance for BTCUSD
        else:
            symbol = "ETHUSD"
            balance = 6000   # Example balance for ETHUSD

        # Adjust trading volume based on balance (example logic)
        volume = 0.1 if balance > 5000 else 0.05

        # Start observing the market
        try:
            while True:
                # Fetch the latest bars data from MT5
                bars = fetch_bars(symbol, mt5.TIMEFRAME_H1, 100)  # Fetching 100 bars for the 1-hour timeframe

                if bars:
                    # Analyze and trade based on the fetched bars and adjusted volume
                    analyze_and_trade(symbol, bars)  # Ensure analyze_and_trade can accept a volume parameter
                else:
                    print("Failed to fetch bars for analysis.")

                # Observe price for specific changes
                observe_price(symbol, pip_diff=15, volume=volume, stop_loss_pips=10)

                # Sleep to avoid hitting rate limits or overloading CPU
                time.sleep(1)  # Check every minute

        except KeyboardInterrupt:
            print("Shutting down the trading script.")
        finally:
            # Properly shutdown MT5 connection
            shutdown_mt5()

def shutdown_mt5():
    print("Closing MT5 connection.")
    mt5.shutdown()

if __name__ == "__main__":
    main()
