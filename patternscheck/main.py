import MetaTrader5 as mt5
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
    weekday_pairs = ['EURUSD']
    return ['BTCUSD'] if weekday in [5, 6] else weekday_pairs


async def trade_symbol(symbol):
    loop = asyncio.get_running_loop()
    pip_diff = 2000 if symbol == 'BTCUSD' else 15
    stop_loss_pips = 1000 if symbol == 'BTCUSD' else 10
    try:
        while True:
            print(f"Fetching bars for {symbol}")
            bars = await loop.run_in_executor(None, fetch_and_aggregate_ticks, symbol, 100, mt5.TIMEFRAME_H1)
            if bars:
                print(f"Bars fetched for {symbol}, {bars}, analyzing trade.")
                analyze_and_trade(symbol, bars)
            else:
                print(f"Failed to fetch bars for {symbol}.")

            print(f"Observing price for {symbol}.")
            await observe_price(symbol, pip_diff=pip_diff, volume=0.1, stop_loss_pips=stop_loss_pips)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in trading symbol {symbol}: {str(e)}")


async def start_trading(symbols):
    tasks = []
    for symbol in symbols:
        print(f"Starting trade task for {symbol}")
        task = asyncio.create_task(trade_symbol(symbol))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print("All trading tasks completed")


def main():
    if connect_to_mt5(ACCOUNT_NUMBER, PASSWORD, SERVER):
        print("Successfully connected to MetaTrader 5.")
        get_account_balance()
        symbols = daily_trading_recommendations()
        print(f"Today's recommended trading pairs: {', '.join(symbols)}")
        asyncio.run(start_trading(symbols))
    mt5.shutdown()

if __name__ == "__main__":
    main()
