import MetaTrader5 as mt5

CANDLE_DATA = 30


def check_price_difference(symbol, pip_size=0.0001, pip_difference=15):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, CANDLE_DATA)

    high = rates[0]['high']
    low = rates[0]['low']

    # Iterate through the rates to find the actual highest and lowest
    for rate in rates:
        if rate['high'] > high:
            high = rate['high']
        if rate['low'] < low:
            low = rate['low']

    current_price = mt5.symbol_info_tick(symbol).ask

    high_diff = abs(high - current_price) / pip_size
    low_diff = abs(current_price - low) / pip_size

    if high_diff <= pip_difference:
        print(
            f"The current price of {symbol} is within {pip_difference} pips of the highest price over the last 1000 candles. Current Price: {current_price}, Highest: {high}")
    elif low_diff <= pip_difference:
        print(
            f"The current price of {symbol} is within {pip_difference} pips of the lowest price over the last 1000 candles. Current Price: {current_price}, Lowest: {low}")
    else:
        print(
            f"No significant price difference observed for {symbol} over the last {CANDLE_DATA} candles. Current Price: {current_price}, Lowest: {low}, Highest: {high}")
