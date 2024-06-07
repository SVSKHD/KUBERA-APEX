import asyncio
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from dhanhq import marketfeed, dhanhq
import datetime
import os

# Credentials
client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

# Dhan client for fetching historical data
dhan = dhanhq(client_id, access_token)

# List of actual symbol names (replace with the actual symbol names)
symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK"]  # Replace these with actual symbols

# Directory to store historical data
data_dir = "historical_data"
os.makedirs(data_dir, exist_ok=True)

# Dictionary to store historical data for all symbols
historical_data = {symbol: pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume']) for symbol in symbols}

# Random Forest model initialization
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Preprocess the data and create features and labels
def preprocess_data(data):
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Invalid data format. Expected a list of dictionaries.")

    df = pd.DataFrame(data)
    if 'datetime' not in df.columns:
        raise ValueError("Invalid data format. 'datetime' column missing.")

    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df['price_diff'] = df['close'].diff()
    df['target'] = df['price_diff'].apply(lambda x: 1 if x > 0 else 0)
    df = df.dropna()
    return df

# Function to make trading decisions
def make_trading_decision(data, model):
    df = preprocess_data(data)
    features = ['open', 'high', 'low', 'close', 'volume']
    X = df[features]
    predictions = model.predict(X)
    df['prediction'] = predictions

    # Calculate moving averages
    df['short_ma'] = df['close'].rolling(window=3).mean()
    df['long_ma'] = df['close'].rolling(window=5).mean()

    # Generate signals
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1

    # Determine entry prices for signals
    df['entry_price'] = df['close']
    df.loc[df['signal'].shift(1) == df['signal'], 'signal'] = 0

    # Map signal to buy/sell
    df['trade_signal'] = df['signal'].map({1: 'Buy', -1: 'Sell', 0: 'Hold'})

    return df[['trade_signal', 'entry_price']]

# Function to handle incoming WebSocket messages
async def on_message(instance, message):
    message_data = json.loads(message)
    symbol = message_data['security_id']
    timestamp = message_data['timestamp']
    open_price = message_data['open']
    high_price = message_data['high']
    low_price = message_data['low']
    close_price = message_data['close']
    volume = message_data['volume']

    # Append the new data to the historical data DataFrame
    new_data = pd.DataFrame([[timestamp, open_price, high_price, low_price, close_price, volume]],
                            columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    historical_data[symbol] = pd.concat([historical_data[symbol], new_data], ignore_index=True)

    # Save the updated DataFrame to a CSV file
    historical_data[symbol].to_csv(os.path.join(data_dir, f"{symbol}.csv"), index=False)

    # Make trading decision
    decision_df = make_trading_decision(historical_data[symbol].to_dict('records'), model)
    latest_decision = decision_df.iloc[-1]
    print(f"Trading decision for {symbol}: {latest_decision['trade_signal']} at {latest_decision['entry_price']}")

# Function to handle WebSocket connection
async def on_connect(instance):
    print("Connected to websocket")

# Function to check if the market is open
def is_market_open():
    current_time = datetime.datetime.now().time()
    market_open_time = datetime.time(9, 15)
    market_close_time = datetime.time(15, 30)
    return market_open_time <= current_time <= market_close_time

# Function to fetch historical data if the market is closed
def fetch_historical_data(symbol, from_date, to_date):
    print(f"Fetching data for {symbol} from {from_date} to {to_date}")
    try:
        data = dhan.historical_daily_data(
            symbol=symbol,
            exchange_segment='NSE_EQ',
            instrument_type='EQUITY',
            expiry_code=0,
            from_date=from_date,
            to_date=to_date
        )
        if 'data' in data and isinstance(data['data'], dict):
            df = pd.DataFrame(data['data'])
            df['datetime'] = pd.to_datetime(df['start_Time'], unit='s')
            df = df.drop(columns=['start_Time'])
            return df.to_dict('records')
        else:
            raise ValueError("Invalid data format fetched from API")
    except Exception as e:
        print(f"Failed to fetch data for {symbol}: {e}")
        return []

# Train the model
def train_model():
    combined_data = []
    for symbol, data in historical_data.items():
        if not data.empty:
            df = preprocess_data(data.to_dict('records'))
            df['symbol'] = symbol
            combined_data.append(df)

    if combined_data:
        combined_df = pd.concat(combined_data)

        # Feature selection
        features = ['open', 'high', 'low', 'close', 'volume']
        X = combined_df[features]
        y = combined_df['target']

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model accuracy: {accuracy:.2f}")
    else:
        print("No data available to train the model.")

# Function to run the WebSocket feed
def run_feed():
    subscription_code = marketfeed.Ticker
    instruments = [(1, symbol) for symbol in symbols]  # Assuming all symbols are in the same exchange segment
    feed = marketfeed.DhanFeed(
        client_id,
        access_token,
        instruments,
        subscription_code,
        on_connect=on_connect,
        on_message=on_message
    )
    feed.run_forever()

# Check if the market is open
if is_market_open():
    print("Market is open. Starting live feed...")
    run_feed()
else:
    print("Market is closed. Fetching historical data...")
    from_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
    to_date = datetime.datetime.now().strftime('%Y-%m-%d')
    for symbol in symbols:
        data = fetch_historical_data(symbol, from_date, to_date)
        if data:
            historical_data[symbol] = pd.DataFrame(data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
            # Save data to CSV
            historical_data[symbol].to_csv(os.path.join(data_dir, f"{symbol}.csv"), index=False)
        else:
            print(f"No historical data found for {symbol}")

    # Train the model initially
    train_model()

    # Make trading decisions based on historical data
    for symbol in symbols:
        if not historical_data[symbol].empty:
            decision_df = make_trading_decision(historical_data[symbol].to_dict('records'), model)
            latest_decision = decision_df.iloc[-1]
            print(f"Trading decision for {symbol}: {latest_decision['trade_signal']} at {latest_decision['entry_price']}")
        else:
            print(f"No data available for {symbol} to make trading decisions.")
