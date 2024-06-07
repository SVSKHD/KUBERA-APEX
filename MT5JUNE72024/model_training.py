import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import joblib
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from connection import initialize_mt5
from fetch_symbols import get_currency_symbols

def get_historical_data(symbol, timeframe, start, end):
    rates = mt5.copy_rates_range(symbol, timeframe, start, end)
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)
    return data

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

def prepare_features_targets(df):
    features = ['open', 'high', 'low', 'close', 'volume', 'sma_20', 'sma_50', 'rsi_14', 'macd', 'bb_upper', 'bb_lower']
    X = df[features]
    y = (df['returns'] > 0).astype(int)
    return X, y

def train_model(symbol, timeframes):
    for timeframe in timeframes:
        print(f"Training model for {symbol} on timeframe {timeframe}...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        data = get_historical_data(symbol, timeframe, start_date, end_date)
        data = preprocess_data(data)
        X, y = prepare_features_targets(data)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = XGBClassifier()
        model.fit(X_train_scaled, y_train)

        joblib.dump(model, f'{symbol}_{timeframe}_model.pkl')
        joblib.dump(scaler, f'{symbol}_{timeframe}_scaler.pkl')

        accuracy = model.score(X_test_scaled, y_test)
        print(f"Model accuracy for {symbol} on timeframe {timeframe}: {accuracy:.2f}")

if __name__ == "__main__":
    login = 212792645
    password = 'pn^eNL4U'
    server = 'OctaFX-Demo'

    if initialize_mt5(login, password, server):
        currency_symbols = get_currency_symbols()
        timeframes = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_H1]
        for symbol in currency_symbols:
            train_model(symbol, timeframes)
        mt5.shutdown()
