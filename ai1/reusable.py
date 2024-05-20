import logging
import smtplib
from email.mime.text import MIMEText
import MetaTrader5 as mt5

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

def place_order(symbol, volume, order_type, price, take_profit, stop_loss):
    try:
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
            log_and_print(f"Order send failed, retcode={result.retcode}")
            send_email("Trading Bot Alert", f"Order send failed, retcode={result.retcode}")
        return result
    except Exception as e:
        log_and_print(f"Error placing order: {e}")
        return None

def close_order(ticket):
    try:
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False
        position = position[0]
        request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'position': ticket,
            'symbol': position.symbol,
            'volume': position.volume,
            'type': mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            'price': mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
            'deviation': 10,
            'magic': 123456,
            'comment': "Closing Position",
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_FOK,
        }
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    except Exception as e:
        log_and_print(f"Error closing order: {e}")
        return False
