import MetaTrader5 as mt5
import pandas as pd

def fetch_data(symbol, timeframe, n_bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        raise ValueError(f"Failed to fetch data for {symbol}")
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    return data

def fetch_multiple_timeframes(symbol, timeframes, n_bars):
    data = {}
    for timeframe in timeframes:
        data[timeframe] = fetch_data(symbol, timeframe, n_bars)
    return data
