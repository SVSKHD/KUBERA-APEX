import MetaTrader5 as mt5
import pandas as pd
from data_fetcher import fetch_data
from indicators import calculate_rsi, calculate_ma, calculate_bollinger_bands
from strategy import identify_levels, generate_signal
from trade_executor import calculate_lot_size


def backtest(symbol, timeframe, n_bars, risk_percentage, stop_loss_pips, initial_balance):
    # Fetch historical data
    data = fetch_data(symbol, timeframe, n_bars)
    data['rsi'] = calculate_rsi(data)
    data['ma'] = calculate_ma(data)
    data['upper_band'], data['lower_band'] = calculate_bollinger_bands(data)

    # Initialize variables
    account_balance = initial_balance
    trade_history = []

    # Simulate trades
    for index in range(1, len(data)):
        current_price = data['close'][index]
        support_level, resistance_level = identify_levels(data.iloc[:index])
        signal = generate_signal(data.iloc[:index], current_price, support_level, resistance_level)

        lot_size = calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol)

        if signal == "BUY":
            stop_loss = support_level
            take_profit = current_price + (50 * mt5.symbol_info(symbol).point)
            result = {
                "symbol": symbol,
                "type": "BUY",
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "lot_size": lot_size
            }
            trade_history.append(result)
            account_balance += (take_profit - current_price) * lot_size

        elif signal == "SELL":
            stop_loss = resistance_level
            take_profit = current_price - (50 * mt5.symbol_info(symbol).point)
            result = {
                "symbol": symbol,
                "type": "SELL",
                "price": current_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "lot_size": lot_size
            }
            trade_history.append(result)
            account_balance += (current_price - take_profit) * lot_size

    return account_balance, trade_history


if __name__ == "__main__":
    # Parameters
    symbol = "GBPUSD"
    timeframe = mt5.TIMEFRAME_H1
    n_bars = 500
    risk_percentage = 1  # Risk 1% of account balance
    stop_loss_pips = 50
    initial_balance = 300

    # Initialize MT5 connection
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()

    final_balance, trades = backtest(symbol, timeframe, n_bars, risk_percentage, stop_loss_pips, initial_balance)

    # Print the results
    print(f"Initial Balance: ${initial_balance}")
    print(f"Final Balance: ${final_balance}")
    print(f"Total Profit: ${final_balance - initial_balance}")

    # Shutdown MT5 connection
    mt5.shutdown()
