import pandas as pd
from pymongo import MongoClient
from datetime import datetime
from dhanhq import DhanHQ

# MongoDB connection placeholder
mongo_url = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"  # Replace with your MongoDB Atlas URL
client = MongoClient(mongo_url)
db = client.KuberaApexDhan  # New database for DhanHQ trades
balance_collection = db.balance_data
loss_recovery_collection = db.loss_recovery
trade_collection = db.dhanhq_trades  # New collection for DhanHQ trades

# Initialize DhanHQ client
api = DhanHQ(client_id='your_client_id', access_token='your_access_token')

def initialize_db():
    # Log database connection success
    print("Database connected successfully")

def load_balance_data():
    balance_data = balance_collection.find_one(sort=[("timestamp", -1)])
    if balance_data:
        if 'losses' not in balance_data:
            balance_data['losses'] = 0.0
            save_balance_data(balance_data)
        return balance_data
    else:
        account_balance = api.get_account_balance()['available_balance']  # Fetch initial balance from DhanHQ
        balance_data = {
            "timestamp": datetime.now(),
            "initial_balance": account_balance,
            "cumulative_gains": 0.0,
            "losses": 0.0  # Track losses
        }
        balance_collection.insert_one(balance_data)
        return balance_data

def save_balance_data(balance_data):
    balance_collection.update_one(
        {"_id": balance_data["_id"]},
        {"$set": balance_data},
        upsert=True
    )

def record_loss_recovery(loss_amount, recovery_amount):
    record = {
        "loss_timestamp": datetime.now(),
        "loss_amount": loss_amount,
        "recovery_timestamp": None,
        "recovery_amount": recovery_amount
    }
    loss_recovery_collection.insert_one(record)

def fetch_daily_losses():
    # Fetch trades from DhanHQ
    trades = api.get_trades(from_date=datetime.now().date(), to_date=datetime.now().date())
    total_loss = sum(abs(trade['net_amount']) for trade in trades if trade['net_amount'] < 0)
    return total_loss

def check_and_log_losses():
    balance_data = balance_collection.find_one(sort=[("timestamp", -1)])
    if balance_data:
        if 'losses' not in balance_data:
            balance_data['losses'] = 0.0
        if balance_data['losses'] == 0:
            daily_loss = fetch_daily_losses()
            if daily_loss > 0:
                balance_data['losses'] = daily_loss
                save_balance_data(balance_data)
                print(f"Logged daily loss: {daily_loss}")
    else:
        balance_data = load_balance_data()
    return balance_data['losses']

def save_trade(trade_data):
    trade_collection.insert_one(trade_data)

def fetch_trades():
    return pd.DataFrame(list(trade_collection.find()))

def record_trade(symbol, transaction_type, quantity, price):
    trade_data = {
        "timestamp": datetime.now(),
        "symbol": symbol,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "price": price
    }
    save_trade(trade_data)

# Example of recording a trade
record_trade('NIFTY', 'BUY', 1, 15000)
