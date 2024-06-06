import MetaTrader5 as mt5
import pandas as pd
import ta
from datetime import datetime
import pytz

# Initialize MetaTrader 5
def initialize_mt5(login, password, server):
    if not mt5.initialize(login=login, password=password, server=server):
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    else:
        print("connected")

# Define symbols and timeframes
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "AUDJPY"]
timeframes = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}

# Function to get historical data for a specific timeframe
def get_historical_data(symbol, timeframe, n_bars=2000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None or len(rates) == 0:
        print(f"No data returned for {symbol} in {timeframe} timeframe")
        return pd.DataFrame()  # Return an empty DataFrame if no data is available
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)
    return data

# Function to preprocess data for a specific timeframe
def preprocess_data(data):
    if data.empty:
        return data
    data['price_change'] = data['close'].pct_change() * 100
    data['price_diff'] = data['close'].diff()
    data['ma5'] = data['close'].rolling(window=5).mean()
    data['ma20'] = data['close'].rolling(window=20).mean()
    data['atr'] = ta.volatility.AverageTrueRange(high=data['high'], low=data['low'], close=data['close']).average_true_range()
    data['rsi'] = ta.momentum.RSIIndicator(close=data['close']).rsi()
    data.dropna(inplace=True)
    data['trend'] = (data['ma5'] > data['ma20']).astype(int)
    data['target'] = (data['price_change'] > 0).astype(int)
    return data

# Function to collect and preprocess data for all symbols and timeframes
def collect_and_preprocess_data():
    all_data = {}
    for symbol in symbols:
        symbol_data = {}
        for tf_name, tf in timeframes.items():
            data = get_historical_data(symbol, tf)
            if data.empty:
                print(f"No data for {symbol} in {tf_name} timeframe")
                continue
            data = preprocess_data(data)
            if data.empty:
                print(f"Preprocessed data for {symbol} in {tf_name} timeframe is empty")
                continue
            symbol_data[tf_name] = data
        if symbol_data:
            all_data[symbol] = symbol_data
    return all_data
