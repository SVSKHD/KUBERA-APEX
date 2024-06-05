import numpy as np
from mt5_handler import get_current_price, place_trade
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd

def calculate_atr(df, period=14):
    df['tr'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift())))
    atr = df['tr'].rolling(window=period).mean()
    return atr

def identify_movements(df, threshold):
    movements = []
    for i in range(1, len(df)):
        price_change = (df['close'][i] - df['close'][i-1]) / df['close'][i-1]
        if price_change > threshold:
            movements.append((df['time'][i], df['close'][i], price_change, 'buy'))
        elif price_change < -threshold:
            movements.append((df['time'][i], df['close'][i], price_change, 'sell'))
    return movements

def calculate_lot_size(balance, risk_percentage, stop_loss):
    risk_amount = balance * risk_percentage
    lot_size = risk_amount / (stop_loss * 100000)  # Assuming 1 pip = 0.0001 for most currency pairs
    return max(0.01, round(lot_size, 2))  # Ensure the minimum lot size is 0.01

def adjust_cooldown_period(volatility):
    cooldown_period_base = 3600  # Base cooldown period in seconds
    return int(cooldown_period_base * (1 + volatility))

def get_trading_symbols():
    symbols_weekday = [
        "EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY",
        "EURGBP", "USDCHF", "AUDUSD", "USDCAD",
        "USDTRY", "USDZAR", "USDBRL", "GBPAUD", "NZDJPY"
    ]
    symbols_weekend = ["BTCUSD", "ETHUSD"]
    today = datetime.now().weekday()
    if today in [5, 6]:  # Saturday (5) and Sunday (6)
        return symbols_weekend, False
    else:
        return symbols_weekday, True

def fetch_all_time_high(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000000)
    df = pd.DataFrame(rates)
    all_time_high = df['high'].max()
    return all_time_high
