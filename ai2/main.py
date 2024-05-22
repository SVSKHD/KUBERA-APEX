import time
import MetaTrader5 as mt5
from connection import initialize_mt5, shutdown_mt5
from data_fetcher import fetch_data
from indicators import calculate_rsi, calculate_ma, calculate_bollinger_bands
from strategy import identify_levels, generate_signal
from trade_executor import calculate_lot_size, place_trade, send_telegram_message

# Parameters
account = 12345678
password = "password"
server = "broker_server"
symbols = ["GBPUSD", "EURUSD"]
timeframe = mt5.TIMEFRAME_H1
n_bars = 500
risk_percentage = 1  # Risk 1% of account balance
stop_loss_pips = 50
bot_token = "your_telegram_bot_token"
chat_id = "your_telegram_chat_id"

# Initialize MT5 connection
if not initialize_mt5(account, password, server):
    raise Exception("Failed to initialize MT5")

# Main loop
try:
    while True:
        for symbol in symbols:
            data = fetch_data(symbol, timeframe, n_bars)
            data['rsi'] = calculate_rsi(data)
            data['ma'] = calculate_ma(data)
            data['upper_band'], data['lower_band'] = calculate_bollinger_bands(data)

            current_price = mt5.symbol_info_tick(symbol).ask
            support_level, resistance_level = identify_levels(data)
            signal = generate_signal(data, current_price, support_level, resistance_level)

            account_balance = mt5.account_info().balance
            lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

            if signal == "BUY":
                stop_loss = support_level
                take_profit = current_price + (50 * mt5.symbol_info(symbol).point)
                result = place_trade(symbol, signal, current_price, stop_loss, take_profit, lot_size)
                send_telegram_message(f"BUY order placed for {symbol} at {current_price}", bot_token, chat_id)
            elif signal == "SELL":
                stop_loss = resistance_level
                take_profit = current_price - (50 * mt5.symbol_info(symbol).point)
                result = place_trade(symbol, signal, current_price, stop_loss, take_profit, lot_size)
                send_telegram_message(f"SELL order placed for {symbol} at {current_price}", bot_token, chat_id)

        time.sleep(3600)  # Run every hour
finally:
    shutdown_mt5()
