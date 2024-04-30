import MetaTrader5 as mt5
import threading
import asyncio
from datetime import datetime
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_bars_async

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'

def daily_trading_recommendations():
    today = datetime.now()
    weekday = today.weekday()  # Monday is 0 and Sunday is 6

    # Define trading pairs for weekends and weekdays
    weekend_pairs = ['BTCUSD']
    weekday_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

    # Check if today is Saturday or Sunday
    if weekday in [5, 6]:  # 5 is Saturday, 6 is Sunday
        return ['BTCUSD']
    else:
        return ['EURUSD', 'GBPUSD', 'USDJPY']

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
            await asyncio.sleep(1)  # Sleep for 1 second to prevent excessive API calls

    loop.run_until_complete(trade_loop())
    loop.close()

def main():
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        symbols = daily_trading_recommendations()
        print(f"Today's recommended trading pairs: {', '.join(symbols)}")

        threads = []
        for symbol in symbols:
            t = threading.Thread(target=trade_symbol, args=(symbol,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

if __name__ == "__main__":
    main()
