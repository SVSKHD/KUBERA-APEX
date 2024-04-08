import MetaTrader5 as mt5

def check_price_difference(symbol, pip_size=0.0001, pip_difference=15):
    """
    Checks if the current price is within a specified pip difference from the latest high or low.

    :param symbol: The symbol to check (e.g., 'EURUSD').
    :param pip_size: The size of a single pip (default is 0.0001, which is standard for most pairs).
    :param pip_difference: The pip difference to check against the high and low (default is 15).
    """
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1)
    if rates is None:
        print(f"Failed to get rates for {symbol}.")
        mt5.shutdown()
        return

    last_rate = rates[0]
    high = last_rate['high']
    low = last_rate['low']
    current_price = mt5.symbol_info_tick(symbol).last

    high_diff = abs(high - current_price) / pip_size
    low_diff = abs(current_price - low) / pip_size

    if high_diff <= pip_difference:
        print(f"The current price of {symbol} is within {pip_difference} pips of the latest high. Current Price: {current_price}, High: {high}")

    if low_diff <= pip_difference:
        print(f"The current price of {symbol} is within {pip_difference} pips of the latest low. Current Price: {current_price}, Low: {low}")

    mt5.shutdown()
