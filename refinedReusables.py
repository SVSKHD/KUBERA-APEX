import MetaTrader5 as mt5
import time


def get_account_balance():
    """Retrieve and print the balance of the connected MT5 account."""
    if not mt5.terminal_info():
        print("Error: Not connected to MT5.")
        return

    account_info = mt5.account_info()
    if account_info is None:
        error_code, error_description = mt5.last_error()
        print(f"Error: Failed to get account info, error code = {error_code}, description = {error_description}")
    else:
        print(f"Account Balance: {account_info.balance}")


def determine_market_trend(symbol_info, current_price):
    # Placeholder function to determine market trend
    # Implement your logic here and return either 'BULLISH' or 'BEARISH'
    # For example, this could be based on moving averages or other indicators
    pass


def trading_logic(symbol, lot, pips_interval, opposite_direction_tolerance):
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} is not available, can not proceed.")
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, can not proceed.")
        return

    entry_price = mt5.symbol_info_tick(symbol).ask
    trade_placed = False
    last_trade_type = None

    try:
        while True:
            current_price = mt5.symbol_info_tick(symbol).ask
            market_trend = determine_market_trend(symbol_info, current_price)

            # Check if the current price has moved 15 pips from the last entry price
            if not trade_placed:
                if market_trend == 'BULLISH' and calculate_pips(current_price, entry_price,
                                                                symbol_info) >= pips_interval:
                    result = order_send(symbol, "BUY", lot, current_price)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"Placing BUY trade at {current_price}")
                        trade_placed = True
                        last_trade_type = "BUY"
                    else:
                        print(f"Failed to place BUY trade at {current_price}")

                elif market_trend == 'BEARISH' and calculate_pips(entry_price, current_price,
                                                                  symbol_info) >= pips_interval:
                    result = order_send(symbol, "SELL", lot, current_price)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        print(f"Placing SELL trade at {current_price}")
                        trade_placed = True
                        last_trade_type = "SELL"
                    else:
                        print(f"Failed to place SELL trade at {current_price}")

            # If the market moves in the opposite direction, close all trades
            if trade_placed:
                pips_moved = calculate_pips(current_price, entry_price, symbol_info)
                if (last_trade_type == "BUY" and pips_moved <= -opposite_direction_tolerance) or \
                        (last_trade_type == "SELL" and pips_moved >= opposite_direction_tolerance):
                    close_all_trades()
                    print("Closed all trades due to adverse price movement.")
                    trade_placed = False
                    last_trade_type = None
                    entry_price = current_price

            time.sleep(1)  # Control the frequency of the while loop

    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        mt5.shutdown()  # Disconnect from the MT5 terminal


# ------------------------------------------------------------------------------- manage-orders
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


def close_position(position):
    """
    Closes a given position.

    :param position: The position object to be closed.
    """
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
        "comment": "Closed by threshold script",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send the trade request
    result = mt5.order_send(close_request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close position {position_id}: {result}")
    else:
        print(f"Position {position_id} closed successfully due to threshold breach.")


def close_trades_on_threshold(account_balance, loss_threshold=0.01, profit_threshold=0.02):
    """
    Closes trades if the profit or loss exceeds the specified thresholds of the account balance.

    :param account_balance: The current account balance.
    :param loss_threshold: The loss threshold as a fraction of the account balance.
    :param profit_threshold: The profit threshold as a fraction of the account balance.
    """
    # Retrieve information about all open positions
    positions = mt5.positions_get()
    if positions is None:
        print("No positions found, error code =", mt5.last_error())
    elif len(positions) > 0:
        for position in positions:
            profit = position.profit
            if profit < 0 and abs(profit) >= account_balance * loss_threshold:
                # Close position if the loss is greater than or equal to 1% of the account balance
                print(f"Closing position {position.ticket} due to a loss threshold breach.")
                close_position(position)
            elif profit > 0 and profit >= account_balance * profit_threshold:
                # Close position if the profit is greater than or equal to 2% of the account balance
                print(f"Closing position {position.ticket} due to a profit threshold breach.")
                close_position(position)


# ---------------------------------------------------------------------------------- main logic
def calculate_pips(price1, price2, symbol_info):
    return (price1 - price2) / symbol_info.point


def trading_logic(symbol, lot, pips_interval, opposite_direction_tolerance):
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} is not available, can not proceed.")
        return

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, can not proceed.")
        return

    entry_price = mt5.symbol_info_tick(symbol).ask

    try:
        while True:
            current_price = mt5.symbol_info_tick(symbol).ask

            # Check if the current price has moved 15 pips from the last entry price
            if calculate_pips(current_price, entry_price, symbol_info) >= pips_interval:
                # Logic to place a trade, this function should be defined elsewhere
                order_send(symbol, "BUY", 0.1, current_price)
                print(f"Placing trade at {current_price}")
                # Update the entry price for the next interval
                entry_price = current_price

            # If the market moves in the opposite direction, close all trades
            if calculate_pips(entry_price, current_price, symbol_info) >= opposite_direction_tolerance:
                close_all_trades()
                print("Closed all trades due to adverse price movement.")
                # Reset the entry price
                entry_price = current_price

            time.sleep(1)  # Control the frequency of the while loop

    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        mt5.shutdown()  # Disconnect from the MT5 terminal
