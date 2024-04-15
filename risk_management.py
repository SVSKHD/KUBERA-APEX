import MetaTrader5 as mt5


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
                print(f"Position {position_id} closed successfully.")


def close_position(ticket):
    # Retrieve position details
    position = mt5.positions_get(ticket=ticket)
    if position is None or len(position) == 0:
        print(f"No position found with ticket ID {ticket}")
        return False

    position = position[0]  # Get the position object from the tuple
    symbol = position.symbol
    lot = position.volume
    position_type = position.type
    deviation = 20  # Acceptable price deviation in points

    # Determine the type of operation required to close the position
    if position_type == mt5.ORDER_TYPE_BUY:
        trade_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        trade_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask

    # Prepare the request dictionary
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": trade_type,
        "price": price,
        "deviation": deviation,
        "magic": 0,  # Identifier of the EA that placed this order, can be set to 0 if N/A
        "comment": f"Closing position {ticket}",
        "type_time": mt5.ORDER_TIME_GTC,  # Good till cancel
        "type_filling": mt5.ORDER_FILLING_FOK,  # Immediate or cancel
    }

    # Send the close order
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close position {ticket}. Error code: {result.retcode}")
        mt5.shutdown()
        return False

    print(f"Position {ticket} closed successfully.")
    return True