import MetaTrader5 as mt5
import time
import schedule
from datetime import datetime, timedelta
from db import MongoDBHandler
from mt5_handler import initialize_mt5, login_mt5, get_account_balance
from data_handler import fetch_data
from trading_logic import calculate_atr, identify_movements, calculate_lot_size, place_trade, adjust_cooldown_period, get_trading_symbols

# Initialize and login to MT5
if not initialize_mt5():
    print("Failed to initialize MT5")
    exit()

if not login_mt5(account=212792645, password='pn^eNL4U', server='OctaFX-Demo'):
    print("Failed to connect to account")
    mt5.shutdown()
    exit()
else:
    print("Connected to MT5 account")

# Fetch account information
initial_balance = get_account_balance()
print(f"Initial balance: {initial_balance}")

# Define symbols and parameters
symbols_weekday = [
    "EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY",
    "EURGBP", "USDCHF", "AUDUSD", "USDCAD",
    "USDTRY", "USDZAR", "USDBRL", "GBPAUD", "NZDJPY"
]
symbols_weekend = ["BTCUSD", "ETHUSD"]
timeframes = [mt5.TIMEFRAME_M15, mt5.TIMEFRAME_H1, mt5.TIMEFRAME_H4]  # Standard timeframes
threshold = 0.092  # Threshold for significant movement
risk_percentage = 0.01  # Risk 1% of account balance per trade
daily_profit_target_low = 0.05  # 5% daily profit target
daily_profit_target_high = 0.10  # 10% daily profit target

# MongoDB setup
db_handler = MongoDBHandler('KuberaApexForex', 'trades', 'daily_summaries')
print("Database connected successfully")

# Track the last trade time for each symbol to enforce cooldown
last_trade_time = {symbol: datetime.min for symbol in symbols_weekday + symbols_weekend}

# Main trading function
def run_trading_bot():
    global last_trade_time
    balance = get_account_balance() or initial_balance
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)  # Fetch data for the last 7 days
    trading_symbols, enforce_profit_target = get_trading_symbols()

    print(f"Monitoring symbols: {trading_symbols}")

    for symbol in trading_symbols:
        for timeframe in timeframes:
            print(f"Fetching data for {symbol} on timeframe {timeframe}")
            df = fetch_data(symbol, timeframe, start_time, end_time)
            if df.empty:
                print(f"No data fetched for {symbol} on timeframe {timeframe}")
                continue

            df['atr'] = calculate_atr(df)
            movements = identify_movements(df, threshold)

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

                    result = place_trade(symbol, action, lot_size, stop_loss, take_profit)
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        print(f"Failed to place trade on {symbol}: {result.comment}")
                        continue

                    # Convert numpy data types to native Python types
                    trade_log = {
                        'date': time,
                        'symbol': symbol,
                        'action': action,
                        'price': float(price),
                        'stop_loss': float(stop_loss),
                        'take_profit': float(take_profit),
                        'balance': float(balance),
                        'lot_size': float(lot_size)
                    }
                    try:
                        db_handler.log_trade(trade_log)
                    except Exception as e:
                        print(f"Failed to log trade for {symbol}: {e}")

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
                try:
                    db_handler.log_daily_summary(daily_summary)
                except Exception as e:
                    print(f"Failed to log daily summary for {symbol}: {e}")

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
