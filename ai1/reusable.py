import logging
import smtplib
from email.mime.text import MIMEText
import MetaTrader5 as mt5
import time


def log_and_print(message):
    logging.info(message)
    print(message)


def send_email(subject, body):
    try:
        smtp_server = "smtp.your-email.com"
        smtp_port = 587
        smtp_user = "your-email@example.com"
        smtp_password = "your-email-password"
        from_email = "your-email@example.com"
        to_email = "recipient-email@example.com"

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        log_and_print(f"Error sending email: {e}")


def retry(func, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            log_and_print(f"Error: {e}, retrying in {delay} seconds...")
            time.sleep(delay)
    raise Exception(f"Failed after {retries} retries")


def place_order(symbol, volume, order_type, price, take_profit, stop_loss):
    def send_order():
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': volume,
            'type': order_type,
            'price': price,
            'tp': take_profit,
            'sl': stop_loss,
            'deviation': 10,
            'magic': 123456,
            'comment': "Adaptive Trading",
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order send failed, retcode={result.retcode}")
        return result

    return retry(send_order)


def close_order(ticket):
    def send_close_order():
        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise Exception(f"Position not found for ticket: {ticket}")
        position = position[0]
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'position': ticket,
            'symbol': position.symbol,
            'volume': position.volume,
            'type': mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            'price': mt5.symbol_info_tick(
                position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(
                position.symbol).ask,
            'deviation': 10,
            'magic': 123456,
            'comment': "Closing Position",
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise Exception(f"Order close failed, retcode={result.retcode}")
        return result

    return retry(send_close_order)
