
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

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
            print(f"Identified upward movement for {df['time'][i]}: {price_change*100:.2f}%")
        elif price_change < -threshold:
            movements.append((df['time'][i], df['close'][i], price_change, 'sell'))
            print(f"Identified downward movement for {df['time'][i]}: {price_change*100:.2f}%")
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
        "EURGBP", "USDCHF", "AUDUSD", "USDCAD", "GBPAUD", "NZDJPY"
    ]
    symbols_weekend = ["BTCUSD", "ETHUSD"]
    today = datetime.now().weekday()
    if today in [5, 6]:  # Saturday (5) and Sunday (6)
        return symbols_weekend, False
    else:
        return symbols_weekday, True

def place_trade(symbol, trade_type, lot_size, price):
    if trade_type == 'buy':
        order_type = mt5.ORDER_TYPE_BUY
    elif trade_type == 'sell':
        order_type = mt5.ORDER_TYPE_SELL
    else:
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed, retcode={result.retcode}")
    else:
        print(f"Trade successful: {result}")

def fetch_all_time_high(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000000)
    df = pd.DataFrame(rates)
    all_time_high = df['high'].max()
    return all_time_high

def identify_volume_spikes(df, volume_threshold):
    spikes = []
    for i in range(1, len(df)):
        if df['volume'][i] > volume_threshold:
            spikes.append((df['time'][i], df['volume'][i], 'spike'))
            print(f"Volume spike identified at {df['time'][i]}: {df['volume'][i]}")
    return spikes
