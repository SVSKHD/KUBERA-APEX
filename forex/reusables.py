# reusables.py
import MetaTrader5 as mt5
import pandas as pd
import datetime

balance = None
no_trade = False


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


def get_open_orders(open_params=None):
    open_orders = mt5.orders_get(**open_params) if open_params else mt5.orders_get()
    if open_orders is None:
        print("reusables.py: No opened orders or failed to retrieve orders, error code =", mt5.last_error())
    else:
        df = pd.DataFrame(list(open_orders), columns=open_orders[0]._asdict().keys())
        print(df)


# order management------------------------
def close_all_trades():
    # Retrieve information about all open positions
    positions = mt5.positions_get()
    if positions is None:
        print("No positions found, error code =", mt5.last_error())
    elif len(positions) > 0:
        for position in positions:
            symbol = position.symbol
            volume = position.volume
            position_id = position.ticket
            trade_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

            # Prepare the request for closing the position
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

            # Send the trade request
            result = mt5.order_send(close_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"Failed to close position {position_id}: {result}")
            else:
                print(f"reusabale.py : Position {position_id} closed successfully.")


# profit and loss trades calculations------
def check_positions_and_close(balance):
    positions = mt5.positions_get()
    if positions is None:
        print("reusables.py: No open positions to check.")
        return

    total_profit = sum(pos.profit for pos in positions)
    profit_or_loss_percentage = (total_profit / balance) * 100  # This works for both profit and loss

    profit_threshold = 0.02 * balance
    loss_threshold = -0.01 * balance

    # Check if the total profit/loss exceeds the thresholds
    if total_profit >= profit_threshold:
        print(
            f"reusables.py: Closing all positions due to profit threshold breach. Total Profit: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")
        close_all_trades()
        no_trade = True
    elif total_profit <= loss_threshold:
        print(
            f"reusables.py: Closing all positions due to loss threshold breach. Total Loss: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")
        close_all_trades()
        no_trade = True
    else:
        print(
            f"We are monitoring the trades. Current Total Profit/Loss: {total_profit} ({profit_or_loss_percentage:.2f}% of balance)")


def mainExecutor(account_number, password, server):
    if connect_to_mt5(account_number, password, server):
        balance = get_account_balance()  # Retrieve and store account balance
        if balance is not None:  # Check if account balance was successfully retrieved
            pairs = print_currency_pairs()  # Retrieve suggested pairs based on the day
            check_positions_and_close(balance)
            if no_trade:
                print(f"Opportunity to trade is open with suggested pairs: {', '.join(pairs)}")
            else:
                print(f"Trades are open, monitoring market with pairs: {', '.join(pairs)}")
    else:
        print("Connection failed or balance not retrieved; unable to suggest pairs.")
