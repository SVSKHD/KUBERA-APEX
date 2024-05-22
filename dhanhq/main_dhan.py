import time
import dhan
from dhan_connection import initialize_dhan
from data_fetcher import fetch_data_dhan
from indicators import calculate_indicators
from dhan_trader_executor import calculate_lot_size, place_order_dhan, close_order_dhan
from strategy import generate_multitimeframe_signal
from concurrent.futures import ThreadPoolExecutor

# Parameters
api_key = "your_api_key"
api_secret = "your_api_secret"
access_token = "your_access_token"
symbols = ["RELIANCE", "TCS", "INFY"]
timeframes = ["1minute", "5minute", "15minute"]  # Multiple timeframes
days = 30
risk_percentage = 1  # Risk 1% of account balance
stop_loss_pips = 10  # Close losing trades at 10 pips in opposite direction
movement_pips = 15  # Place trades for every 15 pips movement
daily_target = 200  # Target profit per day in dollars
initial_balance = 1000
bot_token = "your_telegram_bot_token"
chat_id = "your_telegram_chat_id"

# Initialize Dhan connection
dhan = initialize_dhan(api_key, api_secret, access_token)

def trade_for_symbol(symbol):
    start_balance = initial_balance
    daily_profit = 0
    last_price = None
    active_trades = []

    while daily_profit < daily_target:
        multi_data = {tf: fetch_data_dhan(dhan, symbol, tf, days) for tf in timeframes}
        for tf in multi_data:
            multi_data[tf] = calculate_indicators(multi_data[tf])

        current_price = multi_data['1minute']['close'].iloc[-1]
        signal = generate_multitimeframe_signal(multi_data, current_price)

        account_balance = initial_balance + daily_profit  # Assuming no withdrawals/deposits
        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        # Check for price movement of 15 pips
        if last_price is None or abs(current_price - last_price) >= movement_pips:
            if signal == "BUY":
                stop_loss = current_price - stop_loss_pips
                take_profit = current_price + movement_pips
                place_order_dhan(dhan, symbol, "BUY", current_price, stop_loss, take_profit, lot_size)
                active_trades.append({"symbol": symbol, "action": "BUY", "entry_price": current_price, "stop_loss": stop_loss, "take_profit": take_profit})
            elif signal == "SELL":
                stop_loss = current_price + stop_loss_pips
                take_profit = current_price - movement_pips
                place_order_dhan(dhan, symbol, "SELL", current_price, stop_loss, take_profit, lot_size)
                active_trades.append({"symbol": symbol, "action": "SELL", "entry_price": current_price, "stop_loss": stop_loss, "take_profit": take_profit})

            last_price = current_price

        # Close losing trades
        for trade in active_trades:
            if trade["action"] == "BUY" and current_price <= trade["stop_loss"]:
                close_order_dhan(dhan, trade["symbol"])
                active_trades.remove(trade)
            elif trade["action"] == "SELL" and current_price >= trade["stop_loss"]:
                close_order_dhan(dhan, trade["symbol"])
                active_trades.remove(trade)

        # Update daily profit
        daily_profit = initial_balance + sum([trade["entry_price"] - current_price if trade["action"] == "SELL" else current_price - trade["entry_price"] for trade in active_trades])
        time.sleep(60)  # Check every minute

    print(f"Daily profit target of ${daily_target} reached for {symbol}")

# Main loop to handle multiple symbols
try:
    with ThreadPoolExecutor(max_workers=len(symbols)) as executor:
        executor.map(trade_for_symbol, symbols)
finally:
    print("Shutting down trading bot.")
