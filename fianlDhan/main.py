import time
from db import initialize_db, load_balance_data, save_balance_data, record_trade, check_and_log_losses
from dhanhq import dhanhq
import pandas as pd

# Initialize the API client
api = DhanHQ(client_id='your_client_id', access_token='your_access_token')

def fetch_data(symbol, interval='1h', count=100):
    data = api.get_historical_data(symbol=symbol, interval=interval, count=count)
    return pd.DataFrame(data)

def detect_trend(data, pip_threshold=10):
    data['change'] = data['close'].diff()
    data['movement'] = data['change'].rolling(window=10).sum()
    trend = 'up' if data['movement'].iloc[-1] >= pip_threshold else 'down' if data['movement'].iloc[-1] <= -pip_threshold else 'neutral'
    return trend

def calculate_lot_size(account_balance, risk_percent):
    return (account_balance * risk_percent) / 100

def place_trade(symbol, trend, lot_size):
    price = api.get_quote(symbol)['last_price']
    if trend == 'up':
        order = api.place_order(symbol=symbol, transaction_type='BUY', quantity=lot_size, order_type='MARKET')
    elif trend == 'down':
        order = api.place_order(symbol=symbol, transaction_type='SELL', quantity=lot_size, order_type='MARKET')
    record_trade(symbol, trend, lot_size, price)
    return order

def check_profit_target(balance_data, target_profit_percent=10):
    current_balance = api.get_account_balance()['available_balance']
    initial_balance = balance_data['initial_balance']
    target_profit = initial_balance * (target_profit_percent / 100)
    if current_balance >= initial_balance + target_profit:
        print(f"Target profit of {target_profit_percent}% achieved.")
        return True
    return False

def trading_bot(symbol, interval='1h', count=100, pip_threshold=10, risk_percent=10):
    initialize_db()
    while True:
        data = fetch_data(symbol, interval, count)
        trend = detect_trend(data, pip_threshold)
        balance_data = load_balance_data()
        account_balance = balance_data['initial_balance']
        lot_size = calculate_lot_size(account_balance, risk_percent)
        order = place_trade(symbol, trend, lot_size)
        check_and_log_losses()
        if check_profit_target(balance_data):
            print("Stopping trading bot as target profit achieved.")
            break
        time.sleep(3600)  # Wait for an hour before checking again

# Example usage
trading_bot('NIFTY')
