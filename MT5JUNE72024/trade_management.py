import MetaTrader5 as mt5
import pandas as pd
import joblib
from datetime import datetime
import time
from connection import initialize_mt5
from fetch_symbols import get_currency_symbols

def get_latest_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    return tick

def calculate_percentage_change(previous, current):
    return ((current - previous) / previous) * 100

def preprocess_data(df):
    df['returns'] = df['close'].pct_change()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['rsi_14'] = 100 - (100 / (1 + (
        df['close'].diff(1).rolling(window=14).apply(lambda x: (x[x > 0].sum() / -x[x < 0].sum()), raw=False))))
    df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    df['bb_upper'] = df['sma_20'] + 2 * df['close'].rolling(window=20).std()
    df['bb_lower'] = df['sma_20'] - 2 * df['close'].rolling(window=20).std()
    df.dropna(inplace=True)
    return df

def detect_trend(df):
    if df['sma_20'].iloc[-1] > df['sma_50'].iloc[-1]:
        return 'uptrend'
    elif df['sma_20'].iloc[-1] < df['sma_50'].iloc[-1]:
        return 'downtrend'
    else:
        return 'no trend'

def detect_significant_movement(df, price_threshold=0.003):
    df['price_change'] = df['close'].pct_change()
    df['significant_price_movement'] = (df['price_change'].abs() > price_threshold)
    return df

def monitor_and_trade(symbols, price_threshold=0.003, interval=5):
    while True:
        for symbol in symbols:
            tick = get_latest_tick(symbol)
            if tick is None:
                continue

            current_price = tick.ask
            data = pd.DataFrame({
                'time': [datetime.now()],
                'open': [tick.ask],
                'high': [tick.ask],
                'low': [tick.ask],
                'close': [tick.ask],
                'volume': [tick.volume]
            })
            data.set_index('time', inplace=True)
            data = preprocess_data(data)
            data = detect_significant_movement(data)

            features = ['open', 'high', 'low', 'close', 'volume', 'sma_20', 'sma_50', 'rsi_14', 'macd', 'bb_upper', 'bb_lower']
            X_latest = data[features]

            # Load models and scalers for multiple timeframes
            scaler = joblib.load(f'{symbol}_H1_scaler.pkl')
            model = joblib.load(f'{symbol}_H1_model.pkl')
            X_latest_scaled = scaler.transform(X_latest)
            prediction = model.predict(X_latest_scaled)[-1]

            trend = detect_trend(data)
            last_close = data['close'].iloc[-1]
            second_last_close = data['close'].iloc[-2] if len(data) > 1 else last_close
            percentage_diff = calculate_percentage_change(second_last_close, last_close)

            if trend == 'uptrend' and percentage_diff > price_threshold:
                print(
                    f"{datetime.now()} | {symbol} | Trend: Uptrend | Prediction: Buy | Price: {current_price:.5f} | Percentage Change: {percentage_diff:.2f}%")
            elif trend == 'downtrend' and percentage_diff < -price_threshold:
                print(
                    f"{datetime.now()} | {symbol} | Trend: Downtrend | Prediction: Sell | Price: {current_price:.5f} | Percentage Change: {percentage_diff:.2f}%")

        time.sleep(interval)

if __name__ == "__main__":
    login = 212792645
    password = 'pn^eNL4U'
    server = 'OctaFX-Demo'

    if initialize_mt5(login, password, server):
        try:
            symbols = get_currency_symbols()
            monitor_and_trade(symbols, price_threshold=0.003, interval=5)
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
        finally:
            mt5.shutdown()
