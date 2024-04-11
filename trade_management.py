import MetaTrader5 as mt5


def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price  # Current market price for buy order
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price  # Current market price for sell order

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to find symbol {symbol}, order_send() failed.")
        mt5.shutdown()
        return None

    point = symbol_info.point
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print(f"Invalid order type: {order_type}")
        mt5.shutdown()
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "slippage": slippage,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_FOK,  # Immediate or cancel
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
    else:
        print(f"Order sent successfully, ticket={result.order}")

    return result
