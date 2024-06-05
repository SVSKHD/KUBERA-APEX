import MetaTrader5 as mt5
import pandas as pd

def fetch_data(symbol, timeframe, start_time, end_time):
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)
    return pd.DataFrame(rates)
