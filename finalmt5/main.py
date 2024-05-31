# main.py
import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
import db_operations as db
import numpy as np

# Initialize MT5 connection
mt5.initialize()

# Account login
account = 212792645
password = 'pn^eNL4U'
server = 'OctaFX-Demo'
mt5.login(account, password, server)

# Initialize database
db.initialize_db()


# Function to fetch historical data
def fetch_data(symbol, timeframe, n_bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df


# Function to calculate moving averages
def calculate_moving_averages(df, short_window=5, long_window=20):
    df['short_ma'] = df['close'].rolling(window=short_window).mean()
    df['long_ma'] = df['close'].rolling(window=long_window).mean()
    return df


# Function to detect trend using moving averages
def detect_trend(df):
    df = calculate_moving_averages(df)
    if df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]:
        return 'up'
    elif df['short_ma'].iloc[-1] < df['long_ma'].iloc[-1]:
        return 'down'
    return None


# Function for dynamic lot sizing based on risk
def calculate_lot_size(balance, risk_percentage, stop_loss_pips):
    risk_amount = balance * (risk_percentage / 100)
    lot_size = risk_amount / (stop_loss_pips * 0.0001 * 100000)  # Simplified calculation
    lot_size = max(0.01, round(lot_size, 2))  # Ensure the minimum lot size is 0.01
    print(f"Calculated lot size: {lot_size}")  # Debug log
    return lot_size


# Function to identify candlestick patterns
def identify_candlestick_patterns(df):
    patterns = []
    for i in range(1, len(df) - 1):
        if df['close'][i] > df['open'][i] and df['close'][i] > df['close'][i - 1] and df['close'][i + 1] > df['close'][
            i]:
            patterns.append(('bullish', i))
        elif df['close'][i] < df['open'][i] and df['close'][i] < df['close'][i - 1] and df['close'][i + 1] < \
                df['close'][i]:
            patterns.append(('bearish', i))
    return patterns


# Function to place a trade with dynamic stop loss
def place_trade_with_stop_loss(symbol, trend, lot_size, stop_loss_pips):
    if lot_size == 0:
        print("Lot size is 0, skipping trade")
        return None  # Skip placing the trade if lot size is 0
    order_type = mt5.ORDER_TYPE_BUY if trend == 'up' else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    sl_price = price - (stop_loss_pips * 0.0001) if order_type == mt5.ORDER_TYPE_BUY else price + (
                stop_loss_pips * 0.0001)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl_price,
        "deviation": 10,
        "type_filling": mt5.ORDER_FILLING_FOK
    }
    result = mt5.order_send(request)
    trade_type = "Buy" if order_type == mt5.ORDER_TYPE_BUY else "Sell"
    print(f"Trade placed: {trade_type} for {symbol} at price {price}, Lot size: {lot_size}")
    print(f"Trade result: {result}")  # Debug log
    return result


# Function to manage trades and detect trend reversals
def trade_management(symbol, trend, stop_loss_pips, daily_target, balance_data):
    df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
    current_trend = detect_trend(df)
    if current_trend == trend:
        print(f"Detected trend for {symbol}: {trend}")  # Log the detected trend
        balance = mt5.account_info().balance
        lot_size = calculate_lot_size(balance, 1, stop_loss_pips)  # 1% risk

        # Identify candlestick patterns
        patterns = identify_candlestick_patterns(df)
        for pattern in patterns:
            print(f"Identified pattern: {pattern[0]} at index {pattern[1]} for {symbol}")

        # Check if daily profit target is reached
        while balance_data['cumulative_gains'] < daily_target:
            result_a = place_trade_with_stop_loss(symbol, trend, lot_size, stop_loss_pips)
            if not result_a or result_a.retcode != mt5.TRADE_RETCODE_DONE:
                return  # Trade was not successful

            # Wait for a-b interval
            time.sleep(3600)

            result_b = place_trade_with_stop_loss(symbol, trend, lot_size, stop_loss_pips)
            if not result_b or result_b.retcode != mt5.TRADE_RETCODE_DONE:
                return  # Trade was not successful

            time.sleep(3600)

            result_c = place_trade_with_stop_loss(symbol, trend, lot_size, stop_loss_pips)
            if not result_c or result_c.retcode != mt5.TRADE_RETCODE_DONE:
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
                # Log trade closure
                print(f"Closed all trades for {symbol} due to opposite trend detected")
            # Update balance data and save
            current_balance = mt5.account_info().balance
            balance_data['cumulative_gains'] = current_balance - balance_data['initial_balance']
            if current_balance < balance_data['initial_balance']:
                loss_amount = balance_data['initial_balance'] - current_balance
                balance_data['losses'] += loss_amount
                print(f"Trade closed in loss. Loss amount: {loss_amount}")
                db.record_loss_recovery(loss_amount, 0)
            db.save_balance_data(balance_data)
            # Break loop if daily target is reached
            if balance_data['cumulative_gains'] >= daily_target:
                break


# Function to recover losses and achieve target
def recover_losses_and_target(symbols, balance_data, daily_target_percentage):
    for symbol in symbols:
        while balance_data['losses'] > 0:
            df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
            trend = detect_trend(df)
            if trend:
                print(f"Attempting to recover losses for {symbol} with trend: {trend}")
                balance = mt5.account_info().balance
                daily_target = balance * (daily_target_percentage / 100)
                trade_management(symbol, trend, 10, daily_target, balance_data)
            time.sleep(3600)  # Wait for an hour before checking again

        # Calculate daily target after recovering losses
        balance = mt5.account_info().balance
        daily_target = balance * (daily_target_percentage / 100)

        if balance_data['cumulative_gains'] < daily_target:
            trade_management(symbol, trend, 10, daily_target, balance_data)


# Main trading loop
symbols = ["EURUSD", "GBPUSD"]
daily_target_percentage = 10  # Target 10% of capital per day

balance_data = db.load_balance_data()
db.check_and_log_losses()  # Check and log losses before starting the trading loop

while True:
    recover_losses_and_target(symbols, balance_data, daily_target_percentage)
    for symbol in symbols:
        df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
        trend = detect_trend(df)
        if trend:
            balance = mt5.account_info().balance
            daily_target = balance * (daily_target_percentage / 100)
            trade_management(symbol, trend, 10, daily_target, balance_data)
    time.sleep(3600)  # Wait for an hour before checking again
