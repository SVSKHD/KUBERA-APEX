import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from sklearn.ensemble import VotingClassifier
import ta
import pymongo
import datetime
from dhanhq import dhanhq
from concurrent.futures import ThreadPoolExecutor

# Initialize Dhan API
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTc4MzMxLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.17Ud1DRddoeqtOtENlxwWrVARW0HAOaMvOPihzXoz6aPesUKHEu_IDLevtVIS9krQeUlKKbit_7XeMMMoREbNQ"
client_id = "1100567724"

dhan_api = dhanhq(client_id, access_token)

# MongoDB setup
def get_database():
    CONNECTION_STRING = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"
    client = pymongo.MongoClient(CONNECTION_STRING)
    return client['trading']

def insert_trade(trade):
    db = get_database()
    collection = db['trades']
    collection.insert_one(trade)

# Function to get security IDs from CSV file
def get_security_ids_from_csv(file_path):
    df = pd.read_csv(file_path, low_memory=False)
    print("Columns in CSV:", df.columns)  # Print column names to identify the correct columns
    if 'SEM_SMST_SECURITY_ID' in df.columns and 'SEM_EXCH_INSTRUMENT_TYPE' in df.columns:
        equities = df[df['SEM_EXCH_INSTRUMENT_TYPE'].str.strip() == 'EQ']  # Adjust column value if necessary
        return equities['SEM_SMST_SECURITY_ID'].tolist()
    else:
        # Handle case where the expected columns are not present
        raise ValueError("CSV file does not contain the required 'SEM_SMST_SECURITY_ID' or 'SEM_EXCH_INSTRUMENT_TYPE' columns.")

# Function to get historical data
def get_historical_data(symbol, from_date, to_date):
    response = dhan_api.historical_daily_data(
        symbol=symbol,
        exchange_segment='NSE_EQ',
        instrument_type='EQUITY',
        expiry_code=0,
        from_date=from_date,
        to_date=to_date
    )
    if 'data' in response and 'candles' in response['data']:
        data = pd.DataFrame(response['data']['candles'], columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        data['time'] = pd.to_datetime(data['time'])
        data.set_index('time', inplace=True)
        return data
    else:
        raise ValueError(f"Unexpected response structure for {symbol}: {response}")

# Function to preprocess data
def preprocess_data(data):
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

# Collect and preprocess data for all symbols
def collect_data(security_ids, from_date, to_date):
    all_data = {}
    for security_id in security_ids:
        data = get_historical_data(security_id, from_date, to_date)
        data = preprocess_data(data)
        all_data[security_id] = data
    return all_data

# Function to create and train the model
def train_model(combined_data):
    features = ['open', 'high', 'low', 'close', 'volume', 'price_change', 'trend', 'atr', 'rsi']
    X = combined_data[features]
    y = combined_data['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    lr = LogisticRegression()
    rf = RandomForestClassifier()
    xgb = XGBClassifier()

    ensemble_model = VotingClassifier(estimators=[
        ('lr', lr),
        ('rf', rf),
        ('xgb', xgb)
    ], voting='hard')

    ensemble_model.fit(X_train, y_train)

    y_pred = ensemble_model.predict(X_test)
    print("Ensemble Model Accuracy:", accuracy_score(y_test, y_pred))
    return ensemble_model

# Define the initial capital and daily profit target
initial_capital = 1000
daily_profit_target = initial_capital * 0.02
current_profit = 0

# Function to place trades based on model prediction
def place_trade(security_id, ensemble_model, all_data):
    global current_profit

    account_info = dhan_api.get_account_balance()
    if account_info is None:
        print("Failed to get account info")
        return
    balance = account_info['balance']

    volume = min(1.0, (balance * 0.01) / 100)

    latest_data = all_data[security_id].iloc[-1:]
    latest_data['price_change'] = latest_data['close'].pct_change() * 100
    latest_data['price_diff'] = latest_data['close'].diff()
    latest_data['ma5'] = all_data[security_id]['close'].rolling(window=5).mean().iloc[-1]
    latest_data['ma20'] = all_data[security_id]['close'].rolling(window=20).mean().iloc[-1]
    latest_data['atr'] = ta.volatility.AverageTrueRange(high=latest_data['high'], low=latest_data['low'], close=latest_data['close']).average_true_range().iloc[-1]
    latest_data['rsi'] = ta.momentum.RSIIndicator(close=latest_data['close']).rsi().iloc[-1]
    latest_data.dropna(inplace=True)
    latest_data['trend'] = (latest_data['ma5'] > latest_data['ma20']).astype(int)

    features = ['open', 'high', 'low', 'close', 'volume', 'price_change', 'trend', 'atr', 'rsi']
    latest_features = latest_data[features]

    latest_prediction = ensemble_model.predict(latest_features)

    order_type = 'BUY' if latest_prediction[0] == 1 else 'SELL'
    price = latest_data['close'].iloc[-1]

    result = dhan_api.place_order(
        security_id=security_id,
        exchange_segment=dhan.NSE,  # Assuming NSE, adjust as necessary
        transaction_type=order_type,
        quantity=volume,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=price
    )
    if result['status'] == 'success':
        trade_profit = result['profit']
        current_profit += trade_profit
        print(f"Trade executed for {security_id}: {order_type} {volume} lots at {price}, profit: {trade_profit}, current profit: {current_profit}")
        trade = {
            "security_id": security_id,
            "volume": volume,
            "price": price,
            "order_type": order_type,
            "profit": trade_profit,
            "timestamp": datetime.datetime.utcnow()
        }
        insert_trade(trade)
    else:
        print(f"Failed to execute trade for {security_id}: {result['error']}")

def fetch_live_data(security_ids):
    # Function to fetch live market data
    # Use the live market feed API as per the documentation
    # Reference: https://dhanhq.co/docs/v1/live-market-feed/
    live_data = {}
    for security_id in security_ids:
        response = dhan_api.live_market_data(
            symbol=security_id,
            exchange_segment='NSE_EQ'
        )
        live_data[security_id] = response
    return live_data

def main():
    file_path = './.csv'  # Update this with the correct path to your CSV file
    security_ids = get_security_ids_from_csv(file_path)
    from_date = '2023-01-01'
    to_date = '2024-01-01'
