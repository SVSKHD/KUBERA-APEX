import MetaTrader5 as mt5
import pymongo
from datetime import datetime, timedelta
import time

# Connect to MT5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

account_number = 212792645
password = 'pn^eNL4U'
server = 'OctaFX-Demo'

authorized = mt5.login(account_number, password=password, server=server)
if authorized:
    print("Connected to account")
else:
    print("Failed to connect to account")

# Connect to MongoDB Atlas
client = pymongo.MongoClient(
    "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz")
db = client["trading_bot_db"]
symbols_collection = db["symbols"]
balance_collection = db["balance"]
trades_collection = db["trades"]

# Get available symbols and balance
symbols = mt5.symbols_get()
account_info = mt5.account_info()

# Record symbols and balance in MongoDB
symbols_data = [{"symbol": symbol.name} for symbol in symbols]
symbols_collection.insert_many(symbols_data)
balance_collection.insert_one({"balance": account_info.balance, "timestamp": datetime.now()})


def fetch_symbol_data(symbol, timeframe, num_bars):
    utc_from = datetime.now() - timedelta(days=1)
    rates = mt5.copy_rates_from(symbol, timeframe, utc_from, num_bars)
    return rates


def analyze_data(symbol):
    data_1h = fetch_symbol_data(symbol, mt5.TIMEFRAME_H1, 24)
    data_15m = fetch_symbol_data(symbol, mt5.TIMEFRAME_M15, 96)

    # Ensure there's enough data to analyze
    if len(data_1h) < 4 or len(data_15m) < 4:
        return False

    avg_volume_1h = sum([bar['volume'] for bar in data_1h[-4:-1]]) / 3
    avg_volume_15m = sum([bar['volume'] for bar in data_15m[-4:-1]]) / 3

    volume_change_1h = (data_1h[-1]['volume'] - avg_volume_1h) / avg_volume_1h
    volume_change_15m = (data_15m[-1]['volume'] - avg_volume_15m) / avg_volume_15m

    return volume_change_1h > 0.1 or volume_change_15m > 0.1  # Example threshold of 10%


def place_trade(symbol, lot_size, trade_type, price, order_type="market"):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": trade_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    if order_type == "limit":
        request["type"] = mt5.ORDER_TYPE_BUY_LIMIT if trade_type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL_LIMIT
    elif order_type == "stop":
        request["type"] = mt5.ORDER_TYPE_BUY_STOP if trade_type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL_STOP
    else:
        request["type"] = mt5.ORDER_TYPE_BUY if trade_type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_SELL

    result = mt5.order_send(request)
    return result


def trade_decision(symbol):
    if analyze_data(symbol):
        lot_size = calculate_lot_size(account_info.balance)
        trade_type = mt5.ORDER_TYPE_BUY  # Assuming trade_type based on some condition logic
        current_price = mt5.symbol_info_tick(symbol).ask if trade_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(
            symbol).bid

        # Example: Place a limit order 10 pips above/below current price
        limit_price = current_price + (10 * 0.0001) if trade_type == mt5.ORDER_TYPE_BUY else current_price - (
                    10 * 0.0001)

        result = place_trade(symbol, lot_size, trade_type, limit_price, order_type="limit")
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Limit order placed successfully for {symbol}")
            trades_collection.insert_one(
                {"symbol": symbol, "lot_size": lot_size, "trade_type": trade_type, "order_type": "limit",
                 "timestamp": datetime.now()})
        else:
            print(f"Failed to place limit order for {symbol}: {result.comment}")


def calculate_lot_size(balance):
    risk_amount = balance * 0.02
    lot_size = risk_amount / 1000  # Adjust based on symbol and broker settings
    return lot_size


def main():
    while True:
        for symbol in symbols:
            trade_decision(symbol.name)
        current_balance = mt5.account_info().balance
        balance_collection.insert_one({"balance": current_balance, "timestamp": datetime.now()})
        profit = (current_balance - account_info.balance) / account_info.balance
        if profit >= 0.02:
            print("Daily profit target met")
            break
        time.sleep(3600)  # Check every hour


if __name__ == "__main__":
    main()
