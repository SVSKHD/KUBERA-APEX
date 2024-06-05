import MetaTrader5 as mt5
import pandas as pd
import time

def initialize_mt5():
    return mt5.initialize()

def login_mt5(account, password, server):
    return mt5.login(account, password=password, server=server)

def get_account_balance():
    account_info = mt5.account_info()
    if account_info:
        return account_info.balance
    return None

def get_current_price(symbol, action):
    symbol_info = mt5.symbol_info_tick(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found")
        return None
    if action == "buy":
        return symbol_info.ask
    elif action == "sell":
        return symbol_info.bid
    return None

def place_trade(symbol, action, lot_size, stop_loss, take_profit, retries=3):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} not found, cannot place trade")
        return None

    if not symbol_info.visible:
        print(f"Symbol {symbol} is not visible, making it visible")
        mt5.symbol_select(symbol, True)

    for attempt in range(retries):
        price = get_current_price(symbol, action)
        if price is None:
            print(f"Cannot get current price for {symbol}")
            return None

        if action == "buy":
            order_type = mt5.ORDER_TYPE_BUY
            sl = price - stop_loss
            tp = price + take_profit
        else:
            order_type = mt5.ORDER_TYPE_SELL
            sl = price + stop_loss
            tp = price - take_profit

        if sl <= 0 or tp <= 0:
            print(f"Invalid stop-loss or take-profit levels for {symbol}")
            return None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 234000,
            "comment": "AutoTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
        else:
            print(f"Attempt {attempt + 1} failed for trade on {symbol}: {result.comment}")
            time.sleep(1)  # Wait a bit before retrying

    return result

def fetch_all_time_high(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000000)
    df = pd.DataFrame(rates)
    all_time_high = df['high'].max()
    return all_time_high
