# reusables.py
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import datetime
import time


balance = None
no_open_trade = False


# connecting to forex account
def connect_to_mt5(account_number, password, server):
    if not mt5.initialize():
        print("reusables.py : initialize() failed, error code =", mt5.last_error())
        return False
    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("reusables.py : login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False
    print("reusables.py : Connected to MT5 account #{}".format(account_number))
    return True


def fetch_hourly_bars(symbol, bars_count=1000):
    if not mt5.initialize():
        print("Initialize failed, error code =", mt5.last_error())
        mt5.shutdown()
        return None

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, bars_count)

    if rates is None:
        print("No rates retrieved, error code =", mt5.last_error())
        mt5.shutdown()
        return None

    # Convert to list of dictionaries for easier handling
    bars = [{
        'time': rate['time'],
        'open': rate['open'],
        'high': rate['high'],
        'low': rate['low'],
        'close': rate['close'],
        'volume': rate['tick_volume']
    } for rate in rates]

    mt5.shutdown()  # Ensure MT5 connection is closed after the operation is completed
    return bars

def fetch_and_process_bars_for_symbols(symbols):
    """Fetch bar data for each symbol in the list and store it in a dictionary."""
    print("Processing symbols:", symbols)
    bars_data = {}
    for symbol in symbols:
        bars = fetch_hourly_bars(symbol, 1000)  # Fetch 1000 hourly bars for each symbol
        if bars is not None:
            bars_data[symbol] = bars
            print(f"Successfully fetched bars for {symbol}")
        else:
            print(f"Failed to fetch bars for {symbol}")
    return bars_data


# get balance
def get_account_balance():
    account_info = mt5.account_info()
    if account_info is None:
        print("reusables.py : Failed to get account info, error code =", mt5.last_error())
    else:
        print("reusables.py : Account Balance: ", account_info.balance)
        return account_info.balance


def get_today():
    today = datetime.datetime.now()
    day_name = today.strftime("%A")
    day_number = int(today.strftime("%d"))
    weekday_number = today.isoweekday()

    return day_name, day_number, weekday_number


def print_currency_pairs():
    day_name, day_number, weekday_config = get_today()

    # Check if today is Saturday or Sunday
    if weekday_config in [6, 7]:  # Adjusted to Saturday (6) or Sunday (7)
        pairs = "BTCUSD, ETHUSD"
    else:
        pairs = "EURUSD, GBPUSD, USDJPY"

    print(f"Today is {day_name}, the {day_number}th (Day {weekday_config} of the week). Trading pairs: {pairs}")
    return pairs


def get_open_orders(symbols=None):
    open_params = {}
    if symbols:
        open_params['symbol'] = symbols  # Ensure this key matches the expected key in the MT5 API

    open_orders = mt5.orders_get(**open_params) if open_params else mt5.orders_get()
    if open_orders is None:
        print("No opened orders or failed to retrieve orders, error code =", mt5.last_error())
    else:
        df = pd.DataFrame(list(open_orders), columns=open_orders[0]._asdict().keys())
        print(df)




# candle patterns------------------------
# neutral trend
def is_doji(bar):
    body = abs(bar['close'] - bar['open'])
    candle_range = bar['high'] - bar['low']
    return body <= candle_range * 0.1

# bearish patterns------------------------
def is_evening_star(bars):
    if len(bars) < 3:
        return False

    candle1, candle2, candle3 = bars[-3], bars[-2], bars[-1]
    if candle1['close'] > candle1['open'] and candle3['close'] < candle3['open']:
        if candle2['close'] > candle1['close'] and candle3['close'] < candle2['close'] and candle3['close'] < candle1[
            'open']:
            return True
    return False

def is_dark_cloud_cover(bars):
    if len(bars) < 2:
        return False

    candle1, candle2 = bars[-2], bars[-1]
    if candle1['open'] < candle1['close'] and candle2['open'] > candle1['high'] and candle2['close'] < (
            candle1['open'] + candle1['close']) / 2:
        return True
    return False

def is_engulfing(candle1, candle2):
    if candle1['open'] > candle1['close'] and candle2['open'] < candle2['close']:
        if candle2['open'] <= candle1['close'] and candle2['close'] >= candle1['open']:
            return 'BULLISH'

    elif candle1['open'] < candle1['close'] and candle2['open'] > candle2['close']:
        if candle2['open'] >= candle1['open'] and candle2['close'] <= candle1['close']:
            return 'BEARISH'

    return 'NONE'

# bullish patterns------------------------
def is_hammer(candle):
    # Define the criteria for a hammer
    body = abs(candle['close'] - candle['open'])
    candle_range = candle['high'] - candle['low']
    lower_wick = min(candle['close'], candle['open']) - candle['low']
    upper_wick = candle['high'] - max(candle['close'], candle['open'])

    # Hammer: small body, long lower wick, very small or no upper wick
    return body <= candle_range * 0.3 and lower_wick >= body * 2 and upper_wick <= body * 0.5


def is_morning_star(bars):
    if len(bars) < 3:
        return False

    candle1, candle2, candle3 = bars[-3], bars[-2], bars[-1]
    if candle1['close'] < candle1['open'] and candle3['close'] > candle3['open']:
        if candle2['close'] < candle1['close'] and candle3['close'] > candle2['close'] and candle3['close'] > candle1[
            'open']:
            return True
    return False

def is_piercing_line(bars):
    if len(bars) < 2:
        return False

    candle1, candle2 = bars[-2], bars[-1]
    if candle1['open'] > candle1['close'] and candle2['open'] < candle1['low'] and candle2['close'] > (
            candle1['open'] + candle1['close']) / 2:
        return True
    return False
# order management------------------------
def close_all_trades():
    positions = mt5.positions_get()
    if positions is None:
        print("No positions found, error code =", mt5.last_error())
        return False

    all_closed = True
    global balance  # Ensure balance is accessible globally

    for position in positions:
        symbol = position.symbol
        volume = position.volume
        position_id = position.ticket
        trade_type = mt5.ORDER_TYPE_SELL if position.type == mt4.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": trade_type,
            "position": position_id,
            "magic": 0,
            "comment": "Closed by script",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        result = mt5.order_send(close_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position {position_id}: {result}")
            balance = get_account_balance()  # Update balance after each failed operation
            all_closed = False
        else:
            print(f"reusables.py: Position {position_id} closed successfully.")
            balance = get_account_balance()  # Update balance after each successful operation

    return all_closed


def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Failed to find symbol, order send failed.")
        return None

    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print("Invalid order type.")
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "slippage": slippage,
        "magic": magic,
        "comment": "KUBERA_APEX",
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if not result or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={getattr(result, 'retcode', 'None')}")
        return result

    print(f"Order sent successfully, ticket={result.order}")
    return result

# profit and loss trades calculations------
def check_positions_and_close(symbol,balance):
    print(symbol, balance)
    deals = mt5.positions_total()
    print(deals)
    # positions = mt5.positions_get(symbol)
    # if positions is None:
    #     print(f"reusables.py: No open positions to check.{positions}")
    #     return
    #
    # total_profit = sum(pos.profit for pos in positions)
    # profit_or_loss_percentage = (total_profit / balance) * 100  # This works for both profit and loss
    #
    # profit_threshold = 0.02 * balance
    # loss_threshold = -0.01 * balance
    #
    # # Check if the total profit/loss exceeds the thresholds
    # if total_profit >= profit_threshold:
    #     print(
    #         f"reusables.py: Closing all positions due to profit threshold breach. Total Profit: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")
    #     close_all_trades()
    #     no_open_trade = True
    # elif total_profit <= loss_threshold:
    #     print(
    #         f"reusables.py: Closing all positions due to loss threshold breach. Total Loss: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")
    #     close_all_trades()
    #     no_open_trade = True
    # else:
    #     print(
    #         f"We are monitoring the trades. Current Total Profit/Loss: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")


def mainExecutor(account_number, password, server):
    while True:
        if connect_to_mt5(account_number, password, server):
            balance = get_account_balance()  # Retrieve and store account balance
            if balance is not None:  # Check if account balance was successfully retrieved
                pairs = print_currency_pairs()  # Retrieve suggested pairs based on the day
                symbol_list = pairs.split(", ")
                bars_data = fetch_and_process_bars_for_symbols(symbol_list)
                check_positions_and_close('GBPUSD',balance)
                if no_open_trade:
                    print(f"Opportunity to trade is open with suggested pairs: {pairs}")
                else:
                    print(f"Trades are open, monitoring market with pairs: {pairs}")
        else:
            print("Connection failed or balance not retrieved; unable to suggest pairs.")
    time.sleep(1)
