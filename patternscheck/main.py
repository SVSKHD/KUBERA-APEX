import MetaTrader5 as mt5
import threading
import time
import datetime
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_bars, daily_trading_recommendations

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'


def trade_symbol(symbol):
    while True:
        bars = fetch_bars(symbol, mt5.TIMEFRAME_H1, 100)
        if bars:
            analyze_and_trade(symbol, bars)  # Example fixed volume
        else:
            print(f"Failed to fetch bars for {symbol}.")
        observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10)
        time.sleep(60)  # Sleep to prevent excessive API calls

def main():
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        threads = []
        for symbol in symbols:
            t = threading.Thread(target=trade_symbol, args=(symbol,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()  # Wait for all threads to complete

if __name__ == "__main__":
    main()

