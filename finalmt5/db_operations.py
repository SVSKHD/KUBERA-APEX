# db_operations.py
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import MetaTrader5 as mt5

# MongoDB connection placeholder
mongo_url = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"  # Replace with your MongoDB Atlas URL
client = MongoClient(mongo_url)
db = client.KuberaApexForex
balance_collection = db.balance_data
loss_recovery_collection = db.loss_recovery


def initialize_db():
    # Log database connection success
    print("Database connected successfully")


def load_balance_data():
    balance_data = balance_collection.find_one(sort=[("timestamp", -1)])
    if balance_data:
        return balance_data
    else:
        initial_balance = mt5.account_info().balance
        balance_data = {
            "timestamp": datetime.now(),
            "initial_balance": initial_balance,
            "cumulative_gains": 0.0,
            "losses": 0.0  # Track losses
        }
        balance_collection.insert_one(balance_data)
        return balance_data


def save_balance_data(balance_data):
    balance_data["timestamp"] = datetime.now()
    balance_collection.insert_one(balance_data)


def record_loss_recovery(loss_amount, recovery_amount):
    record = {
        "loss_timestamp": datetime.now(),
        "loss_amount": loss_amount,
        "recovery_timestamp": None,
        "recovery_amount": recovery_amount
    }
    loss_recovery_collection.insert_one(record)


def fetch_daily_losses():
    # Fetch trades from MT5
    today = datetime.now()
    start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today

    trades = mt5.history_deals_get(start_date, end_date)
    if trades is None:
        print("No trades found")
        return 0

    # Calculate total losses
    total_loss = 0
    for trade in trades:
        if trade.profit < 0:
            total_loss += abs(trade.profit)

    return total_loss


def check_and_log_losses():
    balance_data = balance_collection.find_one(sort=[("timestamp", -1)])
    if balance_data and balance_data['losses'] == 0:
        daily_loss = fetch_daily_losses()
        if daily_loss > 0:
            balance_data['losses'] = daily_loss
            save_balance_data(balance_data)
            print(f"Logged daily loss: {daily_loss}")
    return balance_data['losses'] if balance_data else 0
