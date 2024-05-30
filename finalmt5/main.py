import MetaTrader5 as mt5
import pandas as pd
import time

# Initialize MT5 connection
mt5.initialize()

# Account login
ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'
login = mt5.login(ACCOUNT_NUMBER, PASSWORD, SERVER)

if login:
    print("Login successfully")
else:
    print("some Error")


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


# Function to place a trade
def place_trade(symbol, trend, lot_size):
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
    }
    result = mt5.order_send(request)
    return result


# Monitoring and trade management
def trade_management(symbol, trend, interval_pips):
    df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
    current_trend = detect_trend(df)
    if current_trend == trend:
        balance = mt5.account_info().balance
        lot_size = calculate_lot_size(balance, 1)  # 1% risk
        result_a = place_trade(symbol, trend, lot_size)
        if result_a.retcode != mt5.TRADE_RETCODE_DONE:
            return  # Trade was not successful

        # Wait for a-b interval (can be implemented as needed, e.g., sleep for a specific duration or based on new data)
        time.sleep(3600)  # Placeholder for waiting, adjust according to your interval logic

        # Check for b-c interval and place trades
        result_b = place_trade(symbol, trend, lot_size)
        if result_b.retcode != mt5.TRADE_RETCODE_DONE:
            return  # Trade was not successful

        time.sleep(3600)  # Placeholder for waiting, adjust according to your interval logic

        result_c = place_trade(symbol, trend, lot_size)
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


# Main trading loop
symbols = ["EURUSD", "GBPUSD"]
while True:
    for symbol in symbols:
        df = fetch_data(symbol, mt5.TIMEFRAME_H1, 100)
        trend = detect_trend(df)
        if trend:
            trade_management(symbol, trend, 10)
    time.sleep(3600)  # Wait for an hour before checking again
