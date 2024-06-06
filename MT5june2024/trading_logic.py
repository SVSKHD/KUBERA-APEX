import MetaTrader5 as mt5
import time
from datetime import datetime
from pymongo import MongoClient
import threading
from data_collection import get_historical_data, preprocess_data, symbols, timeframes
from model_training import ensemble_model, scaler, model_trained_condition


# MongoDB setup
def get_database():
    CONNECTION_STRING = "mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz"
    client = MongoClient(CONNECTION_STRING)
    return client['trading']


def insert_trade(trade):
    db = get_database()
    collection = db['trades']
    collection.insert_one(trade)


initial_capital = 1000
daily_profit_target = initial_capital * 0.02
current_profit = 0
performance = {symbol: 0 for symbol in symbols}  # Track performance for each symbol


def close_all_trades():
    positions = mt5.positions_get()
    if positions is None:
        print("No open positions to close.")
        return

    for position in positions:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": position.ticket,
            "price": mt5.symbol_info_tick(
                position.symbol).ask if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(
                position.symbol).bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "Auto trade close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position {position.ticket} for {position.symbol}: {result.retcode}")


def calculate_total_profit():
    positions = mt5.positions_get()
    if positions is None:
        return 0
    return sum(position.profit for position in positions)


def place_trade(symbol):
    global current_profit
    global performance

    # Wait until the model is trained
    with model_trained_condition:
        model_trained_condition.wait()

    if ensemble_model is None:
        print("Model is not trained yet")
        return

    # Get account balance
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info")
        return
    balance = account_info.balance

    # Get symbol information to determine minimum volume and step
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to get symbol info for {symbol}")
        return
    min_volume = symbol_info.volume_min
    volume_step = symbol_info.volume_step

    # Calculate the volume to trade (1 lot = 100,000 units of currency)
    volume = max(min_volume, min(1.0, (balance * 0.01) / 1000))  # Risk 1% of balance

    # Ensure volume is a multiple of the volume step
    volume = round(volume / volume_step) * volume_step

    # Get the latest data (fetch more bars to ensure ATR calculation works)
    latest_data_h1 = get_historical_data(symbol, mt5.TIMEFRAME_H1, 20)  # Fetching last 20 bars on 1H timeframe
    latest_data_h1 = preprocess_data(latest_data_h1)

    if latest_data_h1.empty:
        print(f"Not enough data to make a prediction for {symbol}")
        return

    # Prepare features for prediction
    latest_features = latest_data_h1.copy()
    for tf_name, tf in timeframes.items():
        if tf_name != 'H1':
            latest_data_tf = get_historical_data(symbol, tf, 20)
            latest_data_tf = preprocess_data(latest_data_tf)
            if not latest_data_tf.empty:
                for col in latest_data_tf.columns:
                    latest_features[f"{col}_{tf_name}"] = latest_data_tf[col]

    latest_features.dropna(inplace=True)
    if latest_features.empty:
        print(f"Not enough data to make a prediction for {symbol}")
        return

    latest_features_scaled = scaler.transform(latest_features[latest_features.columns.difference(['target'])])

    # Predict
    latest_prediction = ensemble_model.predict(latest_features_scaled)
    prediction_text = "BUY" if latest_prediction[0] == 1 else "SELL"
    print(f"Prediction for {symbol}: {prediction_text}")

    # Place trade based on prediction
    order_type = mt5.ORDER_TYPE_BUY if latest_prediction[0] == 1 else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "Auto trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send the trading request
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        # Wait for the trade to be executed
        time.sleep(2)  # Wait for the trade to be recorded in the account history

        # Retrieve open position
        positions = mt5.positions_get(symbol=symbol)
        if positions is None or len(positions) == 0:
            print(f"Failed to retrieve position info for {symbol}")
            return

        # Calculate profit
        trade_profit = sum(pos.profit for pos in positions)

        # Update current_profit and symbol performance
        current_profit += trade_profit
        performance[symbol] += trade_profit
        print(
            f"Trade executed for {symbol}: {prediction_text} {volume} lots at {price}, profit: {trade_profit}, current profit: {current_profit}")

        # Insert trade into MongoDB
        trade = {
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "order_type": prediction_text,
            "profit": trade_profit,
            "timestamp": datetime.utcnow()
        }
        insert_trade(trade)
    else:
        print(f"Failed to execute trade for {symbol}: {result.retcode}")


def run_trading_bot():
    global current_profit
    while True:
        total_profit = calculate_total_profit()
        if total_profit >= daily_profit_target:
            close_all_trades()
            print(f"Daily profit target achieved. Total profit: {total_profit}. Closing all trades.")
            break

        for symbol in symbols:
            place_trade(symbol)
            total_profit = calculate_total_profit()
            if total_profit >= daily_profit_target:
                close_all_trades()
                print(f"Daily profit target achieved. Total profit: {total_profit}. Closing all trades.")
                break

        # Switch to next symbol if current symbol is not profitable
        symbols.sort(key=lambda x: performance[x])
        time.sleep(3600)  # Wait for an hour before checking again

    # Continue monitoring the market after achieving the daily profit target
    while True:
        for symbol in symbols:
            place_trade(symbol)
        time.sleep(3600)  # Wait for an hour before checking again


# Start the trading thread
trading_thread = threading.Thread(target=run_trading_bot)
trading_thread.start()
