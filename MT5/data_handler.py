import MetaTrader5 as mt5
import pandas as pd

def fetch_data(symbol, timeframe, start_time, end_time):
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)
    if rates is None or len(rates) == 0:
        print(f"No rates returned for {symbol} on timeframe {timeframe}")
        return pd.DataFrame()
    return pd.DataFrame(rates)
