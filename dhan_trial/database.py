from pymongo import MongoClient
import pandas as pd
from datetime import datetime


def create_connection(uri):
    try:
        client = MongoClient(uri)
        db = client['trading_bot']  # Use your database name
        if db is not None:
            print("DB is connected")
        return db
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def store_account_balance(db, balance):
    try:
        db['dhan_account_balance'].insert_one({"balance": balance, "timestamp": datetime.now()})
        print("Account balance stored successfully.")
    except Exception as e:
        print(f"An error occurred while storing account balance: {e}")


def store_trades(db, trades):
    try:
        for trade in trades:
            if 'timestamp' not in trade:
                trade['timestamp'] = datetime.now()
        db['dhan_trades'].insert_many(trades)
        print("Trades stored successfully.")
    except Exception as e:
        print(f"An error occurred while storing trades: {e}")


def store_predictions(db, predictions):
    try:
        for prediction in predictions:
            if 'timestamp' not in prediction:
                prediction['timestamp'] = datetime.now()
        db['dhan_predictions'].insert_many(predictions)
        print("Predictions stored successfully.")
    except Exception as e:
        print(f"An error occurred while storing predictions: {e}")


def store_historical_data(db, dhan, symbols, exchange_segment, instrument_type, from_date, to_date):
    try:
        # Fetch data from dhan (this part depends on your dhan implementation)
        data = fetch_data_from_dhan(dhan, symbols, exchange_segment, instrument_type, from_date, to_date)

        # Ensure 'timestamp' column is present
        for entry in data:
            if 'timestamp' not in entry:
                entry['timestamp'] = datetime.now()

        db['dhan_historical_data'].insert_many(data)
        print("Historical data stored successfully.")
    except Exception as e:
        print(f"An error occurred while storing historical data: {e}")


def fetch_data_from_dhan(dhan, symbols, exchange_segment, instrument_type, from_date, to_date):
    # Mock function to simulate fetching data
    # Replace this with your actual implementation
    return [
        {"symbol": "AAPL", "price": 150},
        {"symbol": "GOOGL", "price": 2800}
    ]
