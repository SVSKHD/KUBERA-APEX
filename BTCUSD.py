import MetaTrader5 as mt5
import math


def adjust_volume(volume, symbol_info):
    if volume < symbol_info.volume_min:
        volume = symbol_info.volume_min
    elif volume > symbol_info.volume_max:
        volume = symbol_info.volume_max

    # Adjust to the nearest valid volume step above the minimum
    normalized_volume = (volume - symbol_info.volume_min) / symbol_info.volume_step
    adjusted_volume = (int(normalized_volume) + 1) * symbol_info.volume_step if normalized_volume % 1 != 0 else normalized_volume * symbol_info.volume_step
    adjusted_volume += symbol_info.volume_min
    return adjusted_volume

def print_symbol_properties(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to find symbol {symbol}.")
        return

    print(f"Trading Conditions for {symbol}:")
    print(f" Minimum volume: {symbol_info.volume_min}")
    print(f" Maximum volume: {symbol_info.volume_max}")
    print(f" Volume step: {symbol_info.volume_step}")
    print(f" Trade is allowed: {symbol_info}")
    print(f" Minimum price change (point size): {symbol_info.point}")


def adjust_price(price, symbol_info):
    """Round price according to the symbol's price point precision."""
    point = symbol_info.point
    price_scale = round(-math.log10(point))
    return round(price, price_scale)

def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Failed to find symbol {symbol}, order_send() failed.")
        return None

    # Fetch the latest price
    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print("Invalid order type.")
        return None

    # Adjust volume and price to meet broker requirements
    volume = adjust_volume(volume, symbol_info)
    price = adjust_price(price, symbol_info)

    # Build the trade request dictionary
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "slippage": slippage,
        "magic": magic,
        "comment": comment,
          "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    # Send the order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={result.retcode} - {mt5.last_error()}")
    else:
        print(f"Order sent successfully, ticket={result.order}")

    return result

# Example Usage
if mt5.initialize():
    print("MT5 initialized")
    print_symbol_properties("BTCUSD")
    order_send("BTCUSD", "BUY", 0.1)
    mt5.shutdown()
else:
    print("Failed to initialize MT5")
