import MetaTrader5 as mt5
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import time as tm
import logging
import ta

# Initialize MT5 connection with provided credentials
if not mt5.initialize(login=212792645, password='pn^eNL4U', server='OctaFX-Demo'):
    print("initialize() failed")
    mt5.shutdown()

# Connect to MongoDB
mongo_client = MongoClient('mongodb+srv://utbiz:utbiz@utbiz.pdnb9ro.mongodb.net/?retryWrites=true&w=majority&appName=utbiz')
db = mongo_client['trading_bot']
collection = db['KUBERA_APEX_FOREX']

# Configure logging
logging.basicConfig(filename='trading_bot.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Trade limits
TRADE_LIMIT_PER_RUN = 3  # Set the maximum number of trades per run

# RSI and MA parameters
RSI_PERIOD = 14
MA_PERIOD_SHORT = 50
MA_PERIOD_LONG = 200
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

def log_and_alert(message):
    logging.info(message)
    print(message)  # Also print the message to the console for real-time feedback

def fetch_data(symbol, timeframe, num_bars):
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)
        if rates is None or len(rates) == 0:
            log_and_alert(f"Failed to fetch data for {symbol} with timeframe {timeframe}")
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    except Exception as e:
        log_and_alert(f"Error fetching data for {symbol} with timeframe {timeframe}: {e}")
        return None

def analyze_indicators(df):
    try:
        df['RSI'] = ta.momentum.RSIIndicator(df['close'], RSI_PERIOD).rsi()
        df['MA_SHORT'] = df['close'].rolling(window=MA_PERIOD_SHORT).mean()
        df['MA_LONG'] = df['close'].rolling(window=MA_PERIOD_LONG).mean()
        return df
    except Exception as e:
        log_and_alert(f"Error analyzing indicators: {e}")
        return None

def check_margin(symbol, lot_size):
    try:
        price = mt5.symbol_info_tick(symbol).ask
        margin = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, symbol, lot_size, price)
        account_info = mt5.account_info()
        return account_info.margin_free >= margin
    except Exception as e:
        log_and_alert(f"Error checking margin for {symbol}: {e}")
        return False

def calculate_lot_size(symbol):
    try:
        account_info = mt5.account_info()
        price = mt5.symbol_info_tick(symbol).ask
        max_margin = account_info.margin_free * 0.01
        if max_margin > 0:
            lot_size = max_margin / price
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                lot_size = max(symbol_info.volume_min, min(lot_size, symbol_info.volume_max))
                lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step  # Adjust to nearest step
            return lot_size
        return 0
    except Exception as e:
        log_and_alert(f"Error calculating lot size for {symbol}: {e}")
        return 0

def place_trade(symbol, action):
    lot_size = calculate_lot_size(symbol)
    if lot_size <= 0 or not check_margin(symbol, lot_size):
        log_and_alert(f"Insufficient margin to place trade for {symbol} with calculated lot size {lot_size}")
        return None

    price = mt5.symbol_info_tick(symbol).ask if action == 'buy' else mt5.symbol_info_tick(symbol).bid
    stop_loss = price - 0.0010 if action == 'buy' else price + 0.0010
    take_profit = price + 0.0020 if action == 'buy' else price - 0.0020

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": 20,
        "magic": 234000,
        "comment": "AutoTrade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        log_and_alert(f"Order failed: {result}")
    else:
        log_and_alert(f"Order placed: {result}")
    return result

def calculate_profit():
    account_info = mt5.account_info()
    return account_info.balance - initial_balance

def risk_management(trade_result):
    return True

def backtest_strategy(symbol, start_date, end_date):
    df = fetch_data(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
    if df is None:
        return 0
    df = analyze_indicators(df)
    if df is None:
        return 0
    profits = []
    for i in range(1, len(df)):
        if df['RSI'].iloc[i] < RSI_OVERSOLD and df['MA_SHORT'].iloc[i] > df['MA_LONG'].iloc[i]:
            profits.append(df['close'].iloc[i+1] - df['close'].iloc[i])
        elif df['RSI'].iloc[i] > RSI_OVERBOUGHT and df['MA_SHORT'].iloc[i] < df['MA_LONG'].iloc[i]:
            profits.append(df['close'].iloc[i] - df['close'].iloc[i+1])
    total_profit = sum(profits)
    log_and_alert(f"Backtest result for {symbol} from {start_date} to {end_date}: {total_profit}")
    return total_profit

def monitor_performance():
    try:
        account_info = mt5.account_info()
        log_and_alert(f"Current balance: {account_info.balance}")
        trades = mt5.history_deals_get(datetime.now() - timedelta(days=1), datetime.now())
        for trade in trades:
            log_and_alert(f"Trade details: {trade}")
    except Exception as e:
        log_and_alert(f"Error monitoring performance: {e}")

def perform_maintenance():
    log_and_alert("Performing maintenance.")

def get_symbols():
    try:
        symbols = [symbol.name for symbol in mt5.symbols_get()]
        if datetime.today().weekday() >= 5:
            crypto_symbols = [symbol for symbol in symbols if "crypto" in symbol.lower()]
            symbols = crypto_symbols
        return symbols
    except Exception as e:
        log_and_alert(f"Error getting symbols: {e}")
        return []

def get_latest_data(symbol):
    timeframes = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_H1]
    data = {}
    for timeframe in timeframes:
        df = fetch_data(symbol, timeframe, 100)
        if df is not None:
            data[timeframe] = df
        else:
            log_and_alert(f"Failed to fetch data for {symbol} with timeframe {timeframe}")
            return None  # Return None if any timeframe data is missing
    return data

def trading_logic():
    global initial_balance
    target_profit = initial_balance * 0.02  # 2% of initial balance
    profit_today = 0
    trades_placed = 0

    symbols = get_symbols()
    for symbol in symbols:
        symbol_data = get_latest_data(symbol)
        if not symbol_data:
            continue  # Skip to the next symbol if data fetching failed
        for timeframe, df in symbol_data.items():
            df = analyze_indicators(df)
            if df is not None and df['RSI'].iloc[-1] < RSI_OVERSOLD and df['MA_SHORT'].iloc[-1] > df['MA_LONG'].iloc[-1]:
                result = place_trade(symbol, 'buy')
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    if risk_management(result):
                        profit_today = calculate_profit()
                        trades_placed += 1
                        collection.update_one(
                            {"date": datetime.now(), "symbol": symbol},
                            {"$push": {"trades": result._asdict()}},
                            upsert=True
                        )
                        log_and_alert(f"Trade placed: {result}")
            elif df is not None and df['RSI'].iloc[-1] > RSI_OVERBOUGHT and df['MA_SHORT'].iloc[-1] < df['MA_LONG'].iloc[-1]:
                result = place_trade(symbol, 'sell')
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    if risk_management(result):
                        profit_today = calculate_profit()
                        trades_placed += 1
                        collection.update_one(
                            {"date": datetime.now(), "symbol": symbol},
                            {"$push": {"trades": result._asdict()}},
                            upsert=True
                        )
                        log_and_alert(f"Trade placed: {result}")
            if profit_today >= target_profit or trades_placed >= TRADE_LIMIT_PER_RUN:
                break
        if profit_today >= target_profit or trades_placed >= TRADE_LIMIT_PER_RUN:
            break

    collection.update_one(
        {"date": datetime.now()},
        {"$set": {"profit_today": profit_today}},
        upsert=True
    )
    log_and_alert(f"Today's profit: {profit_today}")

if __name__ == "__main__":
    account_info = mt5.account_info()
    initial_balance = account_info.balance
    log_and_alert(f"Bot started with balance: {initial_balance}")

    try:
        while True:
            log_and_alert("Running trading logic...")
            trading_logic()
            monitor_performance()
            perform_maintenance()
            log_and_alert("Sleeping for 1 minute...")
            tm.sleep(60)  # Wait for 1 minute before running the next iteration
    except KeyboardInterrupt:
        log_and_alert("Script interrupted by user")
    except Exception as e:
        log_and_alert(f"Error occurred: {e}")
    finally:
        mt5.shutdown()
