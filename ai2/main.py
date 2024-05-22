import time
import MetaTrader5 as mt5
from connection import initialize_mt5, shutdown_mt5
from data_fetcher import fetch_data
from indicators import calculate_rsi, calculate_ma, calculate_bollinger_bands, calculate_macd, calculate_adx
from strategy import identify_levels
from trade_executor import calculate_lot_size, place_trade, send_telegram_message
from model import model_predict

# Parameters
account = 12345678
password = "password"
server = "broker_server"
symbols = ["GBPUSD", "EURUSD", "USDJPY"]
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
            try:
                data = fetch_data(symbol, timeframe, n_bars)
                data['rsi'] = calculate_rsi(data)
                data['ma'] = calculate_ma(data)
                data['upper_band'], data['lower_band'] = calculate_bollinger_bands(data)
                data['macd'], data['macd_signal'] = calculate_macd(data)
                data['adx'] = calculate_adx(data)

                current_price = mt5.symbol_info_tick(symbol).ask
                support_level, resistance_level = identify_levels(data)
                signal = model_predict(data)

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
            except Exception as e:
                print(f"Error processing {symbol}: {e}")

        time.sleep(3600)  # Run every hour
finally:
    shutdown_mt5()
