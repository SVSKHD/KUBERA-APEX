import asyncio
import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from dhanhq import marketfeed
import datetime
import os
from connect import dhan  # Importing the Dhan client
client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

# List of actual symbol names (replace with the actual symbol names)
symbols = ["TCS", "RELIANCE", "INFY", "HDFCBANK"]

# Directory to store historical data
data_dir = "historical_data"
os.makedirs(data_dir, exist_ok=True)

# Dictionary to store historical data for all symbols
historical_data = {symbol: pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume']) for symbol in
                   symbols}

# Random Forest model initialization
model = RandomForestClassifier(n_estimators=100, random_state=42)


# Preprocess the data and create features and labels
def preprocess_data(data):
    df = pd.DataFrame(data)
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


# Check if the market is open and if today is a weekday
def is_weekday():
    today = datetime.datetime.today().weekday()
    return today < 5  # 0 is Monday, 4 is Friday


# Main execution logic
if is_weekday() and is_market_open():
    print("Market is open. Starting live feed...")
    run_feed()
else:
    print("Market is closed. Please run historical_analysis.py for historical data analysis.")
