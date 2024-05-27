import pandas as pd
from data_fetcher import fetch_latest_price


def calculate_moving_average(df, window):
    df[f'ma_{window}'] = df['close'].rolling(window=window).mean()
    return df


def generate_signals(df):
    df['signal'] = 0
    df.loc[df['close'] > df['ma_50'], 'signal'] = 1
    df.loc[df['close'] < df['ma_50'], 'signal'] = -1
    return df


def analyze_data(df):
    df = calculate_moving_average(df, 50)
    df = generate_signals(df)
    return df


def fetch_and_analyze(db, symbol):
    df = pd.DataFrame(list(db.historical_data.find({"symbol": symbol})))
    df = analyze_data(df)
    return df


def get_latest_analysis(db, dhan, symbols, exchange_segment):
    results = {}
    for symbol in symbols:
        latest_price = fetch_latest_price(dhan, symbol, exchange_segment)
        df = fetch_and_analyze(db, symbol)
        latest_signal = df.iloc[-1]['signal']
        results[symbol] = {
            'latest_price': latest_price,
            'latest_signal': latest_signal
        }
    return results
