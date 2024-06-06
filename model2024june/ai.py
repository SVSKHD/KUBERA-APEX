from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
import pytz
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from sklearn.ensemble import VotingClassifier
from sklearn.preprocessing import StandardScaler
import ta
import pymongo
import threading
import time

# Initialize MetaTrader 5
if not mt5.initialize(login=212792645, password='pn^eNL4U', server='OctaFX-Demo'):
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# Define symbols and timeframes
symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]  # Add more symbols as needed
timeframes = {
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}


# MongoDB setup
def get_database():
    CONNECTION_STRING = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"
    client = pymongo.MongoClient(CONNECTION_STRING)
    return client['trading']


def insert_trade(trade):
    db = get_database()
    collection = db['trades']
    collection.insert_one(trade)


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
    data['atr'] = ta.volatility.AverageTrueRange(high=data['high'], low=data['low'],
                                                 close=data['close']).average_true_range()
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


# Initial model and scaler
ensemble_model = None
scaler = StandardScaler()

# Condition variable to synchronize model training and trading
model_trained_condition = threading.Condition()


def train_model():
    global ensemble_model, scaler
    while True:
        all_data = collect_and_preprocess_data()

        combined_data_list = []
        for symbol, symbol_data in all_data.items():
            if 'H1' not in symbol_data or symbol_data['H1'].empty:
                print(f"No H1 data for {symbol}")
                continue
            combined_symbol_data = symbol_data['H1'].copy()
            for tf_name, tf_data in symbol_data.items():
                if tf_name != 'H1':
                    for col in tf_data.columns:
                        combined_symbol_data[f"{col}_{tf_name}"] = tf_data[col]

            # Drop columns with more than 50% NaN values
            combined_symbol_data = combined_symbol_data.dropna(thresh=len(combined_symbol_data) // 2, axis=1)

            print(f"Combined data for {symbol}:")
            print(combined_symbol_data.head())

            if not combined_symbol_data.empty:
                combined_data_list.append(combined_symbol_data)

        if not combined_data_list:
            print("No sufficient data to train the model.")
            time.sleep(3600)
            continue

        combined_data = pd.concat(combined_data_list)
        combined_data.dropna(inplace=True)  # Drop rows with NaN values

        print("Combined data shape after dropping NaN values:", combined_data.shape)
        print(combined_data.head())

        if combined_data.empty:
            print("Combined data is empty after dropping NaN values.")
            time.sleep(3600)
            continue

        # Create features and target
        features = combined_data.columns.difference(['target'])
        X = combined_data[features]
        y = combined_data['target']

        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Train individual models with increased max_iter for Logistic Regression
        lr = LogisticRegression(max_iter=1000)
        rf = RandomForestClassifier()
        xgb = XGBClassifier()

        # Create an ensemble of the models
        ensemble_model = VotingClassifier(estimators=[
            ('lr', lr),
            ('rf', rf),
            ('xgb', xgb)
        ], voting='hard')

        # Train the ensemble model
        ensemble_model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = ensemble_model.predict(X_test)
        print("Ensemble Model Accuracy:", accuracy_score(y_test, y_pred))

        # Notify trading thread that the model is trained
        with model_trained_condition:
            model_trained_condition.notify_all()

        # Retrain every hour
        time.sleep(3600)


# Start the training thread
training_thread = threading.Thread(target=train_model)
training_thread.start()

# Define the initial capital and daily profit target
initial_capital = 1000
daily_profit_target = initial_capital * 0.02
current_profit = 0
performance = {symbol: 0 for symbol in symbols}  # Track performance for each symbol


# Function to place trades based on model prediction
def place_trade(symbol):
    global current_profit
    global performance

    # Wait until the model is trained
    with model_trained_condition:
        model_trained_condition.wait()

    if ensemble_model is None:
        print("Model is not trained yet")
        return

    # Get account balance
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info")
        return
    balance = account_info.balance

    # Get symbol information to determine minimum volume and step
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}")
        return
    min_volume = symbol_info.volume_min
    volume_step = symbol_info.volume_step

    # Calculate the volume to trade (1 lot = 100,000 units of currency)
    volume = max(min_volume, min(1.0, (balance * 0.01) / 1000))  # Risk 1% of balance

    # Ensure volume is a multiple of the volume step
    volume = round(volume / volume_step) * volume_step

    # Get the latest data (fetch more bars to ensure ATR calculation works)
    latest_data_h1 = get_historical_data(symbol, mt5.TIMEFRAME_H1, 20)  # Fetching last 20 bars on 1H timeframe
    latest_data_h1 = preprocess_data(latest_data_h1)

    if latest_data_h1.empty:
        print(f"Not enough data to make a prediction for {symbol}")
        return

    # Prepare features for prediction
    latest_features = latest_data_h1.copy()
    for tf_name, tf in timeframes.items():
        if tf_name != 'H1':
            latest_data_tf = get_historical_data(symbol, tf, 20)
            latest_data_tf = preprocess_data(latest_data_tf)
            if not latest_data_tf.empty:
                for col in latest_data_tf.columns:
                    latest_features[f"{col}_{tf_name}"] = latest_data_tf[col]

    latest_features.dropna(inplace=True)
    if latest_features.empty:
        print(f"Not enough data to make a prediction for {symbol}")
        return

    latest_features_scaled = scaler.transform(latest_features[latest_features.columns.difference(['target'])])

    # Predict
    latest_prediction = ensemble_model.predict(latest_features_scaled)
    prediction_text = "BUY" if latest_prediction[0] == 1 else "SELL"
    print(f"Prediction for {symbol}: {prediction_text}")

    # Place trade based on prediction
    order_type = mt5.ORDER_TYPE_BUY if latest_prediction[0] == 1 else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Auto trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send the trading request
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        # Wait for the trade to be executed
        time.sleep(2)  # Wait for the trade to be recorded in the account history

        # Retrieve open position
        positions = mt5.positions_get(symbol=symbol)
        if positions is None or len(positions) == 0:
            print(f"Failed to retrieve position info for {symbol}")
            return

        # Calculate profit
        trade_profit = sum(pos.profit for pos in positions)

        # Update current_profit and symbol performance
        current_profit += trade_profit
        performance[symbol] += trade_profit
        print(
            f"Trade executed for {symbol}: {prediction_text} {volume} lots at {price}, profit: {trade_profit}, current profit: {current_profit}")

        # Insert trade into MongoDB
        trade = {
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "order_type": prediction_text,
            "profit": trade_profit,
            "timestamp": datetime.utcnow()
        }
        insert_trade(trade)
    else:
        print(f"Failed to execute trade for {symbol}: {result.retcode}")


# Function to run the trading bot
def run_trading_bot():
    global current_profit
    while current_profit < daily_profit_target:
        for symbol in symbols:
            place_trade(symbol)
            if current_profit >= daily_profit_target:
                break
        # Switch to next symbol if current symbol is not profitable
        symbols.sort(key=lambda x: performance[x])
        time.sleep(3600)  # Wait for an hour before checking again


# Start the trading thread
trading_thread = threading.Thread(target=run_trading_bot)
trading_thread.start()

# Shutdown connection to MetaTrader 5
mt5.shutdown()
