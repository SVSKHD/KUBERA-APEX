import MetaTrader5 as mt5
import requests


def calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol):
    risk_amount = account_balance * (risk_percentage / 100)
    symbol_info = mt5.symbol_info(symbol)
    tick_value = symbol_info.point
    lot_size = risk_amount / (stop_loss_pips * tick_value)
    return lot_size


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


def send_telegram_message(message, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Failed to send Telegram message: {response.text}")
    return response.json()
