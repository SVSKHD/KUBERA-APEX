import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from pymongo import MongoClient

# Initialize MT5 connection
mt5.initialize()

# Account login
account = 12345678
password = "your_password"
server = "your_server"
mt5.login(account, password, server)

# MongoDB connection placeholder
mongo_url = "your_mongodb_atlas_url"  # Replace with your MongoDB Atlas URL
client = MongoClient(mongo_url)
db = client.KuberaApexForex
balance_collection = db.balance_data

# Log database connection success
print("Database connected successfully")


# Function to load balance data from MongoDB
def load_balance_data():
    balance_data = balance_collection.find_one(sort=[("timestamp", -1)])
    if balance_data:
        return balance_data
    else:
        initial_balance = mt5.account_info().balance
        balance_data = {
            "timestamp": datetime.now(),
            "initial_balance": initial_balance,
            "cumulative_gains": 0.0
        }
        balance_collection.insert_one(balance_data)
        return balance_data


# Function to save balance data to MongoDB
def save_balance_data(balance_data):
    balance_data["timestamp"] = datetime.now()
    balance_collection.insert_one(balance_data)


# Function to fetch historical data
def fetch_data(symbol, timeframe, n_bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


# Function to detect trend
def detect_trend(df):
    for i in range(len(df) - 1):
        if abs(df['close'][i + 1] - df['close'][i]) >= 10 * 0.0001:
            trend = 'up' if df['close'][i + 1] > df['close'][i] else 'down'
            return trend
    return None


# Function for dynamic lot sizing
def calculate_lot_size(balance, risk_percentage):
    risk_amount = balance * (risk_percentage / 100)
    lot_size = risk_amount / 100000  # Simplified calculation
    return round(lot_size, 2)


# Function to place a trade with trailing stop loss
def place_trade_with_trailing_stop(symbol, trend, lot_size, trailing_stop_pips):
    order_type = mt5.ORDER_TYPE_BUY if trend == 'up' else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "type_filling": mt5.ORDER_FILLING_FOK,
        "sl": price - (trailing_stop_pips * 0.0001) if order_type == mt5.ORDER_TYPE_BUY else price + (
                    trailing_stop_pips * 0.0001)
    }
    result = mt5.order_send(request)
    return result


# Monitoring and trade management
def trade_management(symbol, trend, interval_pips, daily_target, balance_data):
    df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
    current_trend = detect_trend(df)
    if current_trend == trend:
        balance = mt5.account_info().balance
        lot_size = calculate_lot_size(balance, 1)  # 1% risk
        trailing_stop_pips = 10  # Set trailing stop to 10 pips

        # Check if daily profit target is reached
        while balance_data['cumulative_gains'] < daily_target:
            result_a = place_trade_with_trailing_stop(symbol, trend, lot_size, trailing_stop_pips)
            if result_a.retcode != mt5.TRADE_RETCODE_DONE:
                return  # Trade was not successful

            # Wait for a-b interval
            time.sleep(3600)

            result_b = place_trade_with_trailing_stop(symbol, trend, lot_size, trailing_stop_pips)
            if result_b.retcode != mt5.TRADE_RETCODE_DONE:
                return  # Trade was not successful

            time.sleep(3600)

            result_c = place_trade_with_trailing_stop(symbol, trend, lot_size, trailing_stop_pips)
            if result_c.retcode != mt5.TRADE_RETCODE_DONE:
                return  # Trade was not successful

            # Monitoring for opposite direction movement
            opposite_trend_detected = False
            for _ in range(3):  # Check for 3 intervals
                df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
                new_trend = detect_trend(df)
                if new_trend and new_trend != trend:
                    opposite_trend_detected = True
                    break
                time.sleep(3600)  # Wait for next interval

            if opposite_trend_detected:
                # Close all trades to take maximum profits
                positions = mt5.positions_get(symbol=symbol)
                for position in positions:
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": position.volume,
                        "type": mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
                        "position": position.ticket,
                        "price": mt5.symbol_info_tick(
                            symbol).ask if position.type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).bid,
                        "deviation": 10,
                        "type_filling": mt5.ORDER_FILLING_FOK,
                    }
                    mt5.order_send(close_request)
            # Update balance data and save
            balance_data['cumulative_gains'] = mt5.account_info().balance - balance_data['initial_balance']
            save_balance_data(balance_data)
            # Break loop if daily target is reached
            if balance_data['cumulative_gains'] >= daily_target:
                break


# Main trading loop
symbols = ["EURUSD", "GBPUSD"]
daily_target_percentage = 10  # Target 10% of capital per day

balance_data = load_balance_data()
while True:
    for symbol in symbols:
        df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
        trend = detect_trend(df)
        if trend:
            balance = mt5.account_info().balance
            daily_target = balance * (daily_target_percentage / 100)
            trade_management(symbol, trend, 10, daily_target, balance_data)
    time.sleep(3600)  # Wait for an hour before checking again
