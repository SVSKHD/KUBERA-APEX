import time
import MetaTrader5 as mt5
from connection import initialize_mt5, shutdown_mt5
from data_fetcher import fetch_multiple_timeframes
from indicators import calculate_indicators
from trade_executor import calculate_lot_size, place_trade, close_trade, send_telegram_message
from strategy import generate_multitimeframe_signal
from concurrent.futures import ThreadPoolExecutor

# Parameters
account = 212792645
password = 'pn^eNL4U'
server = 'OctaFX-Demo'
symbols = ["EURUSD", "GBPUSD", "USDJPY"]
timeframes = [mt5.TIMEFRAME_M1, mt5.TIMEFRAME_M5, mt5.TIMEFRAME_M15]  # Multiple timeframes
n_bars = 500
risk_percentage = 1  # Risk 1% of account balance
stop_loss_pips = 10  # Close losing trades at 10 pips in opposite direction
movement_pips = 15  # Place trades for every 15 pips movement
daily_target = 200  # Target profit per day in dollars
initial_balance = 1000
bot_token = "your_telegram_bot_token"
chat_id = "your_telegram_chat_id"

# Initialize MT5 connection
if not initialize_mt5(account, password, server):
    raise Exception("Failed to initialize MT5")

def trade_for_symbol(symbol):
    start_balance = mt5.account_info().balance
    daily_profit = 0
    last_price = None
    active_trades = []

    print(f"Observing market for {symbol}...")

    while daily_profit < daily_target:
        multi_data = fetch_multiple_timeframes(symbol, timeframes, n_bars)
        for timeframe in multi_data:
            multi_data[timeframe] = calculate_indicators(multi_data[timeframe])

        current_price = mt5.symbol_info_tick(symbol).ask
        signal = generate_multitimeframe_signal(multi_data, current_price)

        account_balance = mt5.account_info().balance
        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        # Print statements to indicate active market observation
        print(f"Checking market for {symbol} at price {current_price} with signal {signal}...")

        # Check for price movement of 15 pips
        if last_price is None or abs(current_price - last_price) >= movement_pips * mt5.symbol_info(symbol).point:
            if signal == "BUY":
                stop_loss = current_price - stop_loss_pips * mt5.symbol_info(symbol).point
                take_profit = current_price + movement_pips * mt5.symbol_info(symbol).point
                result = place_trade(symbol, "BUY", current_price, stop_loss, take_profit, lot_size)
                active_trades.append(result.order)
                send_telegram_message(f"BUY order placed for {symbol} at {current_price}", bot_token, chat_id)
            elif signal == "SELL":
                stop_loss = current_price + stop_loss_pips * mt5.symbol_info(symbol).point
                take_profit = current_price - movement_pips * mt5.symbol_info(symbol).point
                result = place_trade(symbol, "SELL", current_price, stop_loss, take_profit, lot_size)
                active_trades.append(result.order)
                send_telegram_message(f"SELL order placed for {symbol} at {current_price}", bot_token, chat_id)

            last_price = current_price

        # Close losing trades
        for order in active_trades:
            trade = mt5.positions_get(ticket=order)
            if trade and trade[0].price_current != trade[0].price_open:
                if trade[0].type == mt5.ORDER_TYPE_BUY and current_price <= trade[0].price_open - stop_loss_pips * mt5.symbol_info(symbol).point:
                    close_trade(order)
                    active_trades.remove(order)
                    send_telegram_message(f"BUY order closed for {symbol} at {current_price}", bot_token, chat_id)
                elif trade[0].type == mt5.ORDER_TYPE_SELL and current_price >= trade[0].price_open + stop_loss_pips * mt5.symbol_info(symbol).point:
                    close_trade(order)
                    active_trades.remove(order)
                    send_telegram_message(f"SELL order closed for {symbol} at {current_price}", bot_token, chat_id)

        # Update daily profit
        daily_profit = mt5.account_info().balance - start_balance

        # Print current profit status
        print(f"Current profit for {symbol}: ${daily_profit:.2f}")

        time.sleep(1)  # Check every minute

    print(f"Daily profit target of ${daily_target} reached for {symbol}")

# Main loop to handle multiple symbols
try:
    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        executor.map(trade_for_symbol, symbols)
finally:
    shutdown_mt5()
