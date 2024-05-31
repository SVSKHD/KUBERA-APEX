# db_operations.py
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

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
        "recovery_timestamp": datetime.now(),
        "recovery_amount": recovery_amount
    }
    loss_recovery_collection.insert_one(record)

