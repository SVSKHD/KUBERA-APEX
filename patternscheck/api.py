import MetaTrader5 as mt5


def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    # Initialize MT5 connection if not already initialized
    if not mt5.initialize():
        print("Failed to initialize MT5 API.")
        return None

    # Check if symbol exists in Market Watch
    if not mt5.symbol_select(symbol, True):
        print("Failed to find symbol or add it to market watch, order send failed.")
        mt5.shutdown()
        return None

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Failed to find symbol, order send failed.")
        mt5.shutdown()
        return None

    # Set price and order type based on the symbol and order type
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print("Invalid order type.")
        mt5.shutdown()
        return None

    # Create and send order
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "slippage": slippage,
        "magic": magic,
        "comment": comment,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if not result or result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={getattr(result, 'retcode', 'None')}")
        mt5.shutdown()
        return result

    print(f"Order sent successfully, ticket={result.order}")
    mt5.shutdown()
    return result


# Example usage
order_send("EURUSD", "SELL", 0.1)
