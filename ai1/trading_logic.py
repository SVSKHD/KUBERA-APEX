import MetaTrader5 as mt5
from reusable import log_and_print, place_order, close_order


def get_current_price(symbol):
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            log_and_print(f"Failed to get tick for {symbol}")
            return None, None
        return tick.ask, tick.bid
    except Exception as e:
        log_and_print(f"Error getting current price: {e}")
        return None, None


def get_1h_data(symbol):
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1)
        if rates is None:
            log_and_print(f"Failed to get rates for {symbol}")
            return None
        return rates[0]
    except Exception as e:
        log_and_print(f"Error getting 1-hour data: {e}")
        return None


def calculate_levels(bid_price, ask_price, interval, take_profit):
    buy_price = bid_price - interval * 0.0001
    sell_price = ask_price + interval * 0.0001
    buy_take_profit = buy_price + take_profit * 0.0001
    sell_take_profit = sell_price - take_profit * 0.0001
    buy_stop_loss = buy_price - interval * 0.0001
    sell_stop_loss = sell_price + interval * 0.0001
    return buy_price, sell_price, buy_take_profit, sell_take_profit, buy_stop_loss, sell_stop_loss


def calculate_position_size():
    try:
        account_info = mt5.account_info()
        balance = account_info.balance
        risk_per_trade = 0.01
        stop_loss_pips = 10
        pip_value = 10
        position_size = (balance * risk_per_trade) / (stop_loss_pips * pip_value)
        return position_size
    except Exception as e:
        log_and_print(f"Error calculating position size: {e}")
        return 0.1


def manage_open_positions(symbol, params):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            log_and_print(f"Failed to get positions for {symbol}")
            return

        for position in positions:
            if position.type == mt5.ORDER_TYPE_BUY:
                if get_current_price(symbol)[1] < position.price_open - params['interval'] * 0.0001:
                    close_order(position.ticket)
                    place_order(symbol, position.volume, mt5.ORDER_TYPE_SELL, get_current_price(symbol)[0],
                                get_current_price(symbol)[0] - params['take_profit'] * 0.0001,
                                get_current_price(symbol)[0] + params['interval'] * 0.0001)
            elif position.type == mt5.ORDER_TYPE_SELL:
                if get_current_price(symbol)[0] > position.price_open + params['interval'] * 0.0001:
                    close_order(position.ticket)
                    place_order(symbol, position.volume, mt5.ORDER_TYPE_BUY, get_current_price(symbol)[1],
                                get_current_price(symbol)[1] + params['take_profit'] * 0.0001,
                                get_current_price(symbol)[1] - params['interval'] * 0.0001)
    except Exception as e:
        log_and_print(f"Error managing open positions: {e}")


def update_trailing_stop_loss(symbol):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            log_and_print(f"Failed to get positions for {symbol}")
            return

        for position in positions:
            current_ask, current_bid = get_current_price(symbol)
            if current_ask is None or current_bid is None:
                continue

            if position.type == mt5.ORDER_TYPE_BUY:
                new_stop_loss = current_bid - 10 * 0.0001
                if new_stop_loss > position.sl:
                    mt5.order_modify(position.ticket, stop_loss=new_stop_loss)
            elif position.type == mt5.ORDER_TYPE_SELL:
                new_stop_loss = current_ask + 10 * 0.0001
                if new_stop_loss < position.sl:
                    mt5.order_modify(position.ticket, stop_loss=new_stop_loss)
    except Exception as e:
        log_and_print(f"Error updating trailing stop loss: {e}")
