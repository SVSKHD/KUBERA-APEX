import MetaTrader5 as mt5
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import datetime
import os
import pytz

# MT5 login credentials
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'

# List of actual symbol names
symbols = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]  # Replace these with actual symbols if different
WEEKEND_SYMBOLS = ["BTCUSD", "ETHUSD"]

# Directory to store historical data
data_dir = "historical_data"
os.makedirs(data_dir, exist_ok=True)

# Initialize dictionary to store historical data for all symbols
historical_data = {symbol: pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'tick_volume']) for symbol
                   in symbols}

# Random Forest model initialization
model = RandomForestClassifier(n_estimators=100, random_state=42)


# Initialize MT5 connection
def initialize_mt5():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    authorized = mt5.login(ACCOUNT_NUMBER, password=PASSWORD, server=SERVER)
    if authorized:
        print(f"Connected to account #{ACCOUNT_NUMBER}")
    else:
        print(f"Failed to connect to account #{ACCOUNT_NUMBER}, error code: {mt5.last_error()}")


# Preprocess the data and create features and labels
def preprocess_data(data):
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise ValueError("Invalid data format. Expected a non-empty DataFrame.")

    data['price_diff'] = data['close'].diff()
    data['target'] = data['price_diff'].apply(lambda x: 1 if x > 0 else 0)
    data = data.dropna()
    return data


# Function to make trading decisions
def make_trading_decision(data, model):
    df = preprocess_data(data)
    features = ['open', 'high', 'low', 'close', 'tick_volume']
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


# Function to fetch historical data from MT5
def fetch_historical_data(symbol, from_date, to_date):
    print(f"Fetching data for {symbol} from {from_date} to {to_date}")
    timezone = pytz.timezone("Etc/UTC")
    utc_from = datetime.datetime.strptime(from_date, '%Y-%m-%d').replace(tzinfo=timezone)
    utc_to = datetime.datetime.strptime(to_date, '%Y-%m-%d').replace(tzinfo=timezone)
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, utc_from, utc_to)
    if rates is None:
        print(f"Failed to fetch data for {symbol}, error code: {mt5.last_error()}")
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['datetime'] = pd.to_datetime(df['time'], unit='s')
    df = df.drop(columns=['time'])
    return df


# Train the model
def train_model():
    combined_data = []
    for symbol, data in historical_data.items():
        if not data.empty:
            df = preprocess_data(data)
            df['symbol'] = symbol
            combined_data.append(df)

    if combined_data:
        combined_df = pd.concat(combined_data)

        # Feature selection
        features = ['open', 'high', 'low', 'close', 'tick_volume']
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


# Function to check if the market is open
def is_market_open():
    current_time = datetime.datetime.now().time()
    market_open_time = datetime.time(0, 0)  # Forex market open 24 hours
    market_close_time = datetime.time(23, 59)
    return market_open_time <= current_time <= market_close_time


# Check if the market is open and if today is a weekday
def is_weekday():
    today = datetime.datetime.today().weekday()
    return today < 5  # 0 is Monday, 4 is Friday


# Main execution logic
def main():
    initialize_mt5()
    if is_weekday() and is_market_open():
        print("Market is open. Fetching live data...")
        # Implement live data fetching and decision making if needed
    else:
        print("Market is closed. Fetching historical data...")
        from_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')
        to_date = datetime.datetime.now().strftime('%Y-%m-%d')
        for symbol in symbols:
            data = fetch_historical_data(symbol, from_date, to_date)
            if not data.empty:
                historical_data[symbol] = data
                # Save data to CSV
                historical_data[symbol].to_csv(os.path.join(data_dir, f"{symbol}.csv"), index=False)
            else:
                print(f"No historical data found for {symbol}")

        # Train the model initially
        train_model()

        # Make trading decisions based on historical data
        for symbol in symbols:
            if not historical_data[symbol].empty:
                decision_df = make_trading_decision(historical_data[symbol], model)
                latest_decision = decision_df.iloc[-1]
                print(
                    f"Trading decision for {symbol}: {latest_decision['trade_signal']} at {latest_decision['entry_price']}")
            else:
                print(f"No data available for {symbol} to make trading decisions.")

    mt5.shutdown()


if __name__ == "__main__":
    main()
