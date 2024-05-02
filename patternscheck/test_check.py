# import asyncio
#
# async def simulate_order_send(symbol, order_type, volume):
#     print(f"Order sent: {order_type} {volume} lots of {symbol}")
#
# async def simulate_close_all_trades():
#     print("All trades closed.")
#
# async def observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10):
#     last_traded_price = 1.3000  # Starting price
#     print(f"Starting observation for {symbol} at price: {last_traded_price}")
#     order_type = None
#
#     # Simulating price movements
#     price_changes = [0.0015, -0.0005, 0.0020, -0.0030, 0.0005, 0.0010, -0.0015]
#
#     try:
#         for change in price_changes:
#             await asyncio.sleep(1)  # Simulate time delay
#             current_price = last_traded_price + change
#             pip_scale = 0.0001 if 'JPY' not in symbol else 0.01
#             difference = (current_price - last_traded_price) / pip_scale
#
#             print(f"{symbol} price updated to {current_price:.4f}")
#
#             # Check if the price has moved significantly from the last traded price
#             if abs(difference) >= pip_diff:
#                 direction = "increased" if difference > 0 else "decreased"
#                 print(f"{symbol}: {difference:+.2f} pips {direction} from initial price {last_traded_price:.4f} to {current_price:.4f}")
#                 await simulate_close_all_trades()
#                 order_type = 'BUY' if direction == "increased" else 'SELL'
#                 await simulate_order_send(symbol, order_type, volume)
#                 last_traded_price = current_price  # Update last traded price
#
#             # Monitoring for stop loss condition
#             if order_type:
#                 loss_difference = (current_price - last_traded_price) / pip_scale
#                 if (order_type == 'BUY' and loss_difference <= -stop_loss_pips) or (
#                         order_type == 'SELL' and loss_difference >= stop_loss_pips):
#                     print(f"Market moved {stop_loss_pips} pips against the position; closing all trades.")
#                     await simulate_close_all_trades()
#                     break  # Optional: stop the function after closing trades to reassess strategy
#
#     finally:
#         print("Simulation ended.")
#
# # Usage
# asyncio.run(observe_price("EURUSD"))


dictionary = {
    "symbol": "",
    "last_traded_price": ""
}

print(dictionary)

# import asyncio
#
# async def simulate_order_send(symbol, order_type, volume):
#     print(f"Order sent: {order_type} {volume} lots of {symbol}")
#
# async def simulate_close_all_trades():
#     print("All trades closed.")
#
# async def observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10):
#     last_traded_price = 1.3000 if 'USD' in symbol else 1.7000  # Different starting prices for different symbols
#     print(f"Starting observation for {symbol} at price: {last_traded_price}")
#     order_type = None
#
#     # Generate different dummy price movements for each symbol
#     price_changes = {
#         'EURUSD': [0.0015, -0.0005, 0.0020, -0.0030, 0.0005, 0.0010, -0.0015],
#         'GBPUSD': [0.0008, -0.0020, 0.0007, 0.0030, -0.0003, 0.0012, -0.0010]
#     }
#
#     # Ensure the symbol has price changes defined, otherwise default to a static list
#     symbol_price_changes = price_changes.get(symbol, [0.0001, -0.0001, 0.0002, -0.0002])
#
#     try:
#         for change in symbol_price_changes:
#             await asyncio.sleep(1)  # Simulate time delay
#             current_price = last_traded_price + change
#             pip_scale = 0.0001 if 'JPY' not in symbol else 0.01
#             difference = (current_price - last_traded_price) / pip_scale
#
#             print(f"{symbol} price updated to {current_price:.4f}")
#
#             # Check if the price has moved significantly from the last traded price
#             if abs(difference) >= pip_diff:
#                 direction = "increased" if difference > 0 else "decreased"
#                 print(f"{symbol}: {difference:+.2f} pips {direction} from initial price {last_traded_price:.4f} to {current_price:.4f}")
#                 await simulate_close_all_trades()
#                 order_type = 'BUY' if direction == "increased" else 'SELL'
#                 await simulate_order_send(symbol, order_type, volume)
#                 last_traded_price = current_price  # Update last traded price
#
#             # Monitoring for stop loss condition
#             if order_type:
#                 loss_difference = (current_price - last_traded_price) / pip_scale
#                 if (order_type == 'BUY' and loss_difference <= -stop_loss_pips) or (
#                         order_type == 'SELL' and loss_difference >= stop_loss_pips):
#                     print(f"Market moved {stop_loss_pips} pips against the position; closing all trades.")
#                     await simulate_close_all_trades()
#                     break  # Optional: stop the function after closing trades to reassess strategy
#
#     finally:
#         print(f"Simulation ended for {symbol}.")
#
# # List of symbols to monitor
# symbols = ["EURUSD", "GBPUSD"]
#
# # Creating a list of tasks for each symbol
# tasks = [observe_price(symbol) for symbol in symbols]
#
# # Running all the observation coroutines concurrently
# asyncio.run(asyncio.gather(*tasks));


# check the fetch bars


import MetaTrader5 as mt5
import pandas as pd
import asyncio

# Initialize MetaTrader 5
if not mt5.initialize():
    print("Initialize() failed, error code =", mt5.last_error())
    quit()

# Universal dictionary to store data
data_store = {}


async def async_fetch_data(symbol, timeframe, count):
    """
    Asynchronously fetch data for a single symbol.
    """
    await asyncio.sleep(0)  # Yield control to the event loop
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}, symbol not found on MT5.")
        return None

    # Fetch the latest 100 data points
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        print(f"Failed to get data for {symbol}. Error code={mt5.last_error()}")
        return None

    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


async def fetch_and_store_data(symbols, timeframe=mt5.TIMEFRAME_H1, count=100):
    """
    Asynchronously fetches the latest 100 historical data points for each symbol and updates the global data_store dictionary.

    Args:
        symbols (list): List of symbol strings to fetch data for.
        timeframe (int): Timeframe for historical data, default is one hour (mt5.TIMEFRAME_H1).
        count (int): Number of data points to fetch.
    """
    tasks = [async_fetch_data(symbol, timeframe, count) for symbol in symbols]
    results = await asyncio.gather(*tasks)

    for symbol, df in zip(symbols, results):
        if df is not None:
            data_store[symbol] = df
            print(f"Latest 100 data points for {symbol} updated successfully.")


# Example usage
async def main():
    symbols_to_fetch = ["EURUSD", "GBPUSD", "BTCUSD", "ETHUSD"]
    await fetch_and_store_data(symbols_to_fetch)

    # Example to display the data
    for symbol in symbols_to_fetch:
        if symbol in data_store:
            print(f"Data for {symbol}:\n", data_store[symbol])

    # Shutdown MT5 connection when done
    mt5.shutdown()


# Run the main function
asyncio.run(main())




