import MetaTrader5 as mt5
import requests

ACCOUNT_NUMBER = 212792645
PASSWORD = 'pn^eNL4U'
SERVER = 'OctaFX-Demo'
initial_balance = None

def connect_to_mt5(account_number, password, server , balance):
    global initial_balance
    try:
        if not mt5.initialize():
            print("reusables.py : initialize() failed, error code =", mt5.last_error())
            return False
        authorized = mt5.login(account_number, password=password, server=server)
        if authorized:
            account_info = mt5.account_info()
            if account_info is None:
                print("reusables.py : Failed to get account info, error code =", mt5.last_error())
                mt5.shutdown()
                return False
            balance = account_info.balance
            print("reusables.py : Connected to MT5 account #{} with balance {}".format(account_number, balance))
            return True
        else:
            print("reusables.py : login() failed, error code =", mt5.last_error())
            mt5.shutdown()
            return False
    except Exception as e:
        print(f"reusables.py : An error occurred: {e}")
        mt5.shutdown()
        return False


def place_trade(symbol, action, current_price, stop_loss, take_profit, lot_size):
    deviation = 10
    if action == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
    elif action == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
    else:
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": current_price,
        "sl": stop_loss,
        "tp": take_profit,
        "deviation": deviation,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to execute order: {result.comment}")
    return result


def close_trade(order_ticket):
    position = mt5.positions_get(ticket=order_ticket)
    if not position:
        print(f"No position found with ticket {order_ticket}")
        return

    position = position[0]
    action_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    deviation = 10

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": action_type,
        "position": position.ticket,
        "price": mt5.symbol_info_tick(position.symbol).bid if action_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(position.symbol).ask,
        "deviation": deviation,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close order: {result.comment}")
    return result

def send_telegram_message(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to send Telegram message: {response.text}")
    return response.json()

