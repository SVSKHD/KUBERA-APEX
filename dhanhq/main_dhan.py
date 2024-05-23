import time
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
options_symbols = [
    {"symbol": "RELIANCE", "strike_price": 2500, "option_type": "CALL", "expiry_date": "2024-06-30"},
    {"symbol": "TCS", "strike_price": 3500, "option_type": "PUT", "expiry_date": "2024-06-30"}
]
timeframes = ["1minute", "5minute", "15minute"]
days = 30
risk_percentage = 1
stop_loss_pips = 10
movement_pips = 15
daily_target = 200
initial_balance = 1000

# Initialize Dhan connection
dhan = initialize_dhan(api_key, api_secret, access_token)

def estimate_profit(entry_price, take_profit, lot_size, direction):
    if direction == "BUY":
        return (take_profit - entry_price) * lot_size
    elif direction == "SELL":
        return (entry_price - take_profit) * lot_size

def select_best_trades(dhan, symbols, options_symbols, timeframes, days, risk_percentage, stop_loss_pips, movement_pips, initial_balance):
    best_trades = []

    # Check equity symbols
    for symbol in symbols:
        multi_data = {tf: fetch_data_dhan(dhan, symbol, tf, days) for tf in timeframes}
        for tf in multi_data:
            multi_data[tf] = calculate_indicators(multi_data[tf])

        current_price = multi_data['1minute']['close'].iloc[-1]
        signal = generate_multitimeframe_signal(multi_data, current_price)

        account_balance = initial_balance
        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        if signal == "BUY":
            stop_loss = current_price - stop_loss_pips
            take_profit = current_price + movement_pips
            estimated_profit = estimate_profit(current_price, take_profit, lot_size, "BUY")
            best_trades.append({
                "symbol": symbol,
                "action": "BUY",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "estimated_profit": estimated_profit,
                "lot_size": lot_size,
                "is_option": False
            })
        elif signal == "SELL":
            stop_loss = current_price + stop_loss_pips
            take_profit = current_price - movement_pips
            estimated_profit = estimate_profit(current_price, take_profit, lot_size, "SELL")
            best_trades.append({
                "symbol": symbol,
                "action": "SELL",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "estimated_profit": estimated_profit,
                "lot_size": lot_size,
                "is_option": False
            })

    # Check options symbols
    for option in options_symbols:
        symbol = option["symbol"]
        strike_price = option["strike_price"]
        option_type = option["option_type"]
        expiry_date = option["expiry_date"]
        multi_data = {tf: fetch_data_dhan(dhan, symbol, tf, days, is_option=True, strike_price=strike_price, option_type=option_type, expiry_date=expiry_date) for tf in timeframes}
        for tf in multi_data:
            multi_data[tf] = calculate_indicators(multi_data[tf])

        current_price = multi_data['1minute']['close'].iloc[-1]
        signal = generate_multitimeframe_signal(multi_data, current_price)

        account_balance = initial_balance
        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        if signal == "BUY":
            stop_loss = current_price - stop_loss_pips
            take_profit = current_price + movement_pips
            estimated_profit = estimate_profit(current_price, take_profit, lot_size, "BUY")
            best_trades.append({
                "symbol": symbol,
                "action": "BUY",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "estimated_profit": estimated_profit,
                "lot_size": lot_size,
                "is_option": True,
                "strike_price": strike_price,
                "option_type": option_type,
                "expiry_date": expiry_date
            })
        elif signal == "SELL":
            stop_loss = current_price + stop_loss_pips
            take_profit = current_price - movement_pips
            estimated_profit = estimate_profit(current_price, take_profit, lot_size, "SELL")
            best_trades.append({
                "symbol": symbol,
                "action": "SELL",
                "entry_price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "estimated_profit": estimated_profit,
                "lot_size": lot_size,
                "is_option": True,
                "strike_price": strike_price,
                "option_type": option_type,
                "expiry_date": expiry_date
            })

    best_trades.sort(key=lambda x: x["estimated_profit"], reverse=True)
    return best_trades

def trade_for_symbol(dhan, trade):
    symbol = trade["symbol"]
    action = trade["action"]
    entry_price = trade["entry_price"]
    stop_loss = trade["stop_loss"]
    take_profit = trade["take_profit"]
    lot_size = trade["lot_size"]
    is_option = trade["is_option"]

    if is_option:
        strike_price = trade["strike_price"]
        option_type = trade["option_type"]
        expiry_date = trade["expiry_date"]
        place_order_dhan(dhan, symbol, action, entry_price, stop_loss, take_profit, lot_size, is_option=True, strike_price=strike_price, option_type=option_type, expiry_date=expiry_date)
    else:
        place_order_dhan(dhan, symbol, action, entry_price, stop_loss, take_profit, lot_size)

    return trade

# Main loop to handle multiple symbols
try:
    best_trades = select_best_trades(dhan, symbols, options_symbols, timeframes, days, risk_percentage, stop_loss_pips, movement_pips, initial_balance)

    start_balance = initial_balance
    daily_profit = 0
    active_trades = []

    while daily_profit < daily_target:
        if not best_trades:
            print("No suitable trades found.")
            break

        trade = best_trades.pop(0)
        active_trades.append(trade_for_symbol(dhan, trade))

        # Fetch the latest price for the active trades
        for trade in active_trades:
            current_price = fetch_data_dhan(dhan, trade["symbol"], "1minute", 1, is_option=trade["is_option"], strike_price=trade.get("strike_price"), option_type=trade.get("option_type"), expiry_date=trade.get("expiry_date"))['close'].iloc[-1]
            if trade["action"] == "BUY" and current_price <= trade["stop_loss"]:
                close_order_dhan(dhan, trade["symbol"], is_option=trade["is_option"])
                active_trades.remove(trade)
            elif trade["action"] == "SELL" and current_price >= trade["stop_loss"]:
                close_order_dhan(dhan, trade["symbol"], is_option=trade["is_option"])
                active_trades.remove(trade)

        # Update daily profit based on closed trades
        daily_profit = sum([
            (trade["take_profit"] - trade["entry_price"]) * trade["lot_size"] if trade["action"] == "BUY" else
            (trade["entry_price"] - trade["take_profit"]) * trade["lot_size"]
            for trade in active_trades if
            (trade["action"] == "BUY" and current_price >= trade["take_profit"]) or
            (trade["action"] == "SELL" and current_price <= trade["take_profit"])
        ])
        time.sleep(60)

    print(f"Daily profit target of ${daily_target} reached.")
finally:
    print("Shutting down trading bot.")
