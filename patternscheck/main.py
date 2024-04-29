import MetaTrader5 as mt5
import threading
import time
import asyncio
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_bars_async, daily_trading_recommendations

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'

def trade_symbol(symbol):
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def trade_loop():
        while True:
            bars = await fetch_bars_async(symbol, mt5.TIMEFRAME_H1, 100)
            if bars:
                analyze_and_trade(symbol, bars)
            else:
                print(f"Failed to fetch bars for {symbol}.")
            observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10)
            await asyncio.sleep(60)  # Sleep to prevent excessive API calls

    loop.run_until_complete(trade_loop())
    loop.close()

def main():
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        recommendation = daily_trading_recommendations()
        print(recommendation)

        # Deciding symbols based on recommendation (example logic)
        symbols = ['BTCUSD'] if 'weekend' in recommendation else ['EURUSD', 'GBPUSD','USDJPY']

        threads = []
        for symbol in symbols:
            t = threading.Thread(target=trade_symbol, args=(symbol,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

if __name__ == "__main__":
    main()
