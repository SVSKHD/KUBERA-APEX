
import MetaTrader5 as mt5
import time
import schedule
from datetime import datetime, timedelta
from db import MongoDBHandler
from mt5_handler import initialize_mt5, login_mt5, get_account_balance
from data_handler import fetch_data
from trading_logic import calculate_atr, identify_movements, calculate_lot_size, place_trade, adjust_cooldown_period, get_trading_symbols, identify_volume_spikes

# Initialize and login to MT5
if not initialize_mt5():
    print("Failed to initialize MT5")
    exit()

if not login_mt5(account=212792645, password='pn^eNL4U', server='OctaFX-Demo'):
    print("Failed to connect to account")
    exit()
else:
    print("connected")

db_handler = MongoDBHandler(db_name='Kuberaapexdhan', trade_collection_name='trades', daily_summary_collection_name='daily_summaries')

def execute_trading_logic():
    symbols, is_weekday = get_trading_symbols()
    volume_threshold = 1000  # Example threshold, adjust as needed
    for symbol in symbols:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        df = fetch_data(symbol, mt5.TIMEFRAME_H1, start_time, end_time)
        
        if df.empty:
            continue

        atr = calculate_atr(df)
        movements = identify_movements(df, threshold=0.001)
        volume_spikes = identify_volume_spikes(df, volume_threshold)

        for spike in volume_spikes:
            spike_time, volume, event_type = spike
            account_balance = get_account_balance()
            lot_size = calculate_lot_size(account_balance, risk_percentage=0.01, stop_loss=atr.iloc[-1])
            place_trade(symbol, 'buy', lot_size, df['close'].iloc[-1])
            db_handler.log_trade({
                'symbol': symbol,
                'time': spike_time,
                'type': 'buy',
                'price': df['close'].iloc[-1],
                'lot_size': lot_size
            })

        for movement in movements:
            trade_time, trade_price, price_change, trade_type = movement
            account_balance = get_account_balance()
            lot_size = calculate_lot_size(account_balance, risk_percentage=0.01, stop_loss=atr.iloc[-1])
            place_trade(symbol, trade_type, lot_size, trade_price)
            db_handler.log_trade({
                'symbol': symbol,
                'time': trade_time,
                'type': trade_type,
                'price': trade_price,
                'lot_size': lot_size
            })

schedule.every().hour.do(execute_trading_logic)

while True:
    schedule.run_pending()
    time.sleep(1)
