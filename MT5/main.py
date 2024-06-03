import MetaTrader5 as mt5
import pandas as pd
import time
import schedule
from datetime import datetime, timedelta
from db import MongoDBHandler
import numpy as np

# Initialize MT5 and connect
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# Login to your account (replace with your details)
account = 212792645
password = 'pn^eNL4U'
server = 'OctaFX-Demo'
if not mt5.login(account, password=password, server=server):
    print("Failed to connect to account.")
    mt5.shutdown()
else:
    print("Connected to MT5 account")

# Define symbols and parameters
symbols_weekday = [
    "EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY",
    "EURGBP", "USDCHF", "AUDUSD", "USDCAD",
]
symbols_weekend = ["BTCUSD", "ETHUSD"]
timeframes = [mt5.TIMEFRAME_M15, mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H4]  # Multi-timeframe analysis
threshold = 0.001  # Threshold for significant movement
initial_balance = 1000  # Starting balance in USD
risk_percentage = 0.01  # Risk 1% of account balance per trade
cooldown_period_base = 3600  # Base cooldown period in seconds
daily_profit_target_low = 0.05  # 5% daily profit target
daily_profit_target_high = 0.10  # 10% daily profit target
retry_attempts = 3  # Number of retry attempts for failed trades

# MongoDB setup
db_handler = MongoDBHandler('KuberaApexForex', 'trades', 'daily_summaries')
print("Database connected successfully")

# Function to fetch data
def fetch_data(symbol, timeframe, start_time, end_time):
    rates = mt5.copy_rates_range(symbol, timeframe, start_time, end_time)
    return pd.DataFrame(rates)

# Function to calculate ATR (Average True Range)
def calculate_atr(df, period=14):
    df['tr'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift()), abs(df['low'] - df['close'].shift())))
    atr = df['tr'].rolling(window=period).mean()
    return atr

# Function to identify significant movements (refined)
def identify_movements(df):
    movements = []
    for i in range(1, len(df)):
        price_change = (df['close'][i] - df['close'][i-1]) / df['close'][i-1]
        if price_change > threshold:
            movements.append((df['time'][i], df['close'][i], price_change, 'buy'))
        elif price_change < -threshold:
            movements.append((df['time'][i], df['close'][i], price_change, 'sell'))
    return movements

# Function to calculate dynamic lot size
def calculate_lot_size(balance, risk_percentage, stop_loss):
    risk_amount = balance * risk_percentage
    lot_size = risk_amount / (stop_loss * 100000)  # Assuming 1 pip = 0.0001 for most currency pairs
    return max(0.01, round(lot_size, 2))  # Ensure the minimum lot size is 0.01

# Function to place a trade with stop-loss and take-profit
def place_trade(symbol, action, lot_size, price, stop_loss, take_profit, retries=retry_attempts):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found, cannot place trade")
        return None

    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, making it visible")
        mt5.symbol_select(symbol, True)

    for attempt in range(retries):
        if action == "buy":
            order_type = mt5.ORDER_TYPE_BUY
            sl = price - stop_loss
            tp = price + take_profit
        else:
            order_type = mt5.ORDER_TYPE_SELL
            sl = price + stop_loss
            tp = price - take_profit

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": "AutoTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
        else:
            print(f"Attempt {attempt + 1} failed for trade on {symbol}: {result.comment}")
            time.sleep(1)  # Wait a bit before retrying

    return result

# Determine the current day and set symbols
def get_trading_symbols():
    today = datetime.now().weekday()
    if today in [5, 6]:  # Saturday (5) and Sunday (6)
        return symbols_weekend, False
    else:
        return symbols_weekday, True

# Function to adjust cooldown period based on market conditions
def adjust_cooldown_period(volatility):
    # Adjust cooldown period based on the ATR (volatility)
    return int(cooldown_period_base * (1 + volatility))

# Track last trade time for cooldown
last_trade_time = {symbol: datetime.min for symbol in symbols_weekday + symbols_weekend}

# Main trading function
def run_trading_bot():
    global last_trade_time
    account_info = mt5.account_info()
    balance = account_info.balance if account_info else initial_balance
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)  # Fetch data for the last 7 days
    trading_symbols, enforce_profit_target = get_trading_symbols()

    print(f"Monitoring symbols: {trading_symbols}")

    for symbol in trading_symbols:
        for timeframe in timeframes:
            df = fetch_data(symbol, timeframe, start_time, end_time)
            df['atr'] = calculate_atr(df)
            movements = identify_movements(df)

            for movement in movements:
                time, price, price_change, action = movement
                is_favorable = abs(price_change) > threshold
                print(f"Observing {symbol} at {time} with price {price:.5f}, price change {price_change*100:.2f}%, favorable: {is_favorable}, decision: {action}")

                if (datetime.now() - last_trade_time[symbol]).total_seconds() > adjust_cooldown_period(df['atr'].iloc[-1]):
                    atr = df['atr'].iloc[-1]
                    stop_loss = atr * 2  # 2 ATR stop loss
                    take_profit = atr * 4  # 4 ATR take profit
                    lot_size = calculate_lot_size(balance, risk_percentage, stop_loss)

                    print(f"Placing trade on {symbol} with price change {price_change*100:.2f}%, action: {action}")

                    result = place_trade(symbol, action, lot_size, price, stop_loss, take_profit)
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print(f"Failed to place trade on {symbol}: {result.comment}")
                        continue

                    # Log the trade in MongoDB
                    trade_log = {
                        'date': time,
                        'symbol': symbol,
                        'action': action,
                        'price': price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'balance': balance,
                        'lot_size': lot_size
                    }
                    db_handler.log_trade(trade_log)

                    # Update last trade time
                    last_trade_time[symbol] = datetime.now()

                    print(f"Trade placed on {symbol} at {price:.5f}, action: {action}, lot size: {lot_size:.2f}")

                # Calculate daily profit
                daily_profit = balance - initial_balance
                profit_target_achieved = daily_profit >= initial_balance * daily_profit_target_low and daily_profit <= initial_balance * daily_profit_target_high if enforce_profit_target else None
                daily_summary = {
                    'date': end_time.date(),
                    'symbol': symbol,
                    'initial_balance': initial_balance,
                    'final_balance': balance,
                    'daily_profit': daily_profit,
                    'profit_target_achieved': profit_target_achieved
                }
                db_handler.log_daily_summary(daily_summary)

# Schedule the trading bot to run every minute
schedule.every().minute.do(run_trading_bot)

# Main execution loop
if __name__ == "__main__":
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by User")
    finally:
        db_handler.print_trade_logs()
        db_handler.print_daily_summaries()
        mt5.shutdown()
