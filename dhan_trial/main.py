from connection import initialize_dhan
from data_fetcher import store_historical_data, fetch_latest_price
from analyzer import get_latest_analysis
from database import create_connection, store_account_balance, store_trades, store_predictions
import pandas as pd


# Parameters
client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

symbols = ["TCS", "RELIANCE", "INFY"]
exchange_segment = "NSE_EQ"
instrument_type = "EQUITY"
from_date = "2022-01-08"
to_date = "2022-02-08"
mongodb_uri = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"

# Initialize Dhan connection
dhan = initialize_dhan(client_id, access_token)


# Connect to MongoDB
db = create_connection(mongodb_uri)

# # Store historical data
store_historical_data(db, dhan, symbols, exchange_segment, instrument_type, from_date, to_date)

# # Fetch and analyze latest data
results = get_latest_analysis(db, dhan, symbols, exchange_segment)

# Example: Store account balance
account_balance = 100000  # Replace with actual value fetched from API
store_account_balance(db, account_balance)

# Example: Store trades (dummy data)
trades = [{"symbol": "TCS", "action": "BUY", "price": 3500, "quantity": 10, "timestamp": pd.Timestamp.now()}]
store_trades(db, trades)

# Example: Store predictions (dummy data)
predictions = [{"symbol": "TCS", "predicted_price": 3600, "timestamp": pd.Timestamp.now()}]
store_predictions(db, predictions)

print("Latest Analysis Results:")
for symbol, result in results.items():
    print(f"Symbol: {symbol}")
    print(f"  Latest Price: {result['latest_price']}")
    print(f"  Latest Signal: {result['latest_signal']}")
