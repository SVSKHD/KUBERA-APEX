import pandas as pd
from indicators import calculate_indicators
from strategy import generate_multitimeframe_signal
from dhan_connection import initialize_dhan
from data_fetcher import  fetch_data_dhan

def backtest(dhan, symbol, timeframes, days, risk_percentage, stop_loss_pips, movement_pips, initial_balance):
    multi_data = {tf: fetch_data_dhan(dhan, symbol, tf, days) for tf in timeframes}
    for tf in multi_data:
        multi_data[tf] = calculate_indicators(multi_data[tf])

    current_price = multi_data['1minute']['close'].iloc[-1]
    signal = generate_multitimeframe_signal(multi_data, current_price)

    account_balance = initial_balance
    daily_profit = 0
    last_price = None
    active_trades = []

    for i in range(len(multi_data['1minute'])):
        current_price = multi_data['1minute']['close'].iloc[i]

        # Update signals based on new data
        signal = generate_multitimeframe_signal(multi_data, current_price)

        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        # Check for price movement of 15 pips
        if last_price is None or abs(current_price - last_price) >= movement_pips:
            if signal == "BUY":
                stop_loss = current_price - stop_loss_pips
                take_profit = current_price + movement_pips
                active_trades.append(
                    {"symbol": symbol, "action": "BUY", "entry_price": current_price, "stop_loss": stop_loss,
                     "take_profit": take_profit})
            elif signal == "SELL":
                stop_loss = current_price + stop_loss_pips
                take_profit = current_price - movement_pips
                active_trades.append(
                    {"symbol": symbol, "action": "SELL", "entry_price": current_price, "stop_loss": stop_loss,
                     "take_profit": take_profit})

            last_price = current_price

        # Close losing trades
        for trade in active_trades:
            if trade["action"] == "BUY" and current_price <= trade["stop_loss"]:
                account_balance -= (trade["entry_price"] - current_price) * lot_size
                active_trades.remove(trade)
            elif trade["action"] == "SELL" and current_price >= trade["stop_loss"]:
                account_balance -= (current_price - trade["entry_price"]) * lot_size
                active_trades.remove(trade)

        # Update daily profit
        daily_profit = account_balance - initial_balance

    return daily_profit, account_balance


# Example usage
if __name__ == "__main__":
    api_key = "your_api_key"
    api_secret = "your_api_secret"
    access_token = "your_access_token"
    dhan = initialize_dhan(api_key, api_secret, access_token)

    symbol = "RELIANCE"
    timeframes = ["1minute", "5minute", "15minute"]
    days = 30
    risk_percentage = 1
    stop_loss_pips = 10
    movement_pips = 15
    initial_balance = 1000

    daily_profit, final_balance = backtest(dhan, symbol, timeframes, days, risk_percentage, stop_loss_pips,
                                           movement_pips, initial_balance)
    print(f"Daily Profit: {daily_profit}, Final Balance: {final_balance}")
