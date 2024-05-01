import MetaTrader5 as mt5
import threading
import asyncio
from datetime import datetime
from reusables import connect_to_mt5, get_account_balance, analyze_and_trade, observe_price, fetch_and_aggregate_ticks

# Configuration for MT5 connection
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'


def daily_trading_recommendations():
    today = datetime.now()
    weekday = today.weekday()


    weekend_pairs = ['BTCUSD']
    weekday_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'NZDUSD', 'USDCAD', 'EURJPY', 'GBPJPY']

    if weekday in [5, 6]:  # Saturday or Sunday
        return ['BTCUSD']
    else:
        return weekday_pairs  # Updated to return the expanded list


async def trade_symbol(symbol):
    loop = asyncio.get_running_loop()

    if symbol == 'BTCUSD':
        pip_diff = 2000
        stop_loss_pips = 1000
    else:
        pip_diff = 15
        stop_loss_pips = 10

    while True:
        bars = await loop.run_in_executor(None, fetch_and_aggregate_ticks, symbol, 100, mt5.TIMEFRAME_H1)
        if bars:
            analyze_and_trade(symbol, bars)
        else:
            print(f"Failed to fetch bars for {symbol}.")

        observe_price(symbol, pip_diff=pip_diff, volume=0.1, stop_loss_pips=stop_loss_pips)
        await asyncio.sleep(1)


def main():
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()

        symbols = daily_trading_recommendations()
        print(f"Today's recommended trading pairs: {', '.join(symbols)}")

        threads = []
        for symbol in symbols:
            t = threading.Thread(target=lambda: asyncio.run(trade_symbol(symbol)))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()


if __name__ == "__main__":
    main()
