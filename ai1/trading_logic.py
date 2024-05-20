import MetaTrader5 as mt5
from reusable import log_and_print, place_order, close_order
import concurrent.futures
import time
from datetime import datetime
import talib


def get_current_price(symbol):
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Failed to get tick for {symbol}")
        return tick.ask, tick.bid
    except Exception as e:
        log_and_print(f"Error getting current price for {symbol}: {e}")
        return None, None


def get_1h_data(symbol):
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None:
            raise ValueError(f"Failed to get rates for {symbol}")
        return rates
    except Exception as e:
        log_and_print(f"Error getting 1-hour data for {symbol}: {e}")
        return None


def calculate_levels(bid_price, ask_price, interval, take_profit, volatility):
    try:
        atr = volatility * 0.0001  # ATR as a pip value
        buy_price = bid_price - atr
        sell_price = ask_price + atr
        buy_take_profit = buy_price + take_profit * 0.0001
        sell_take_profit = sell_price - take_profit * 0.0001
        buy_stop_loss = buy_price - atr
        sell_stop_loss = sell_price + atr
        return buy_price, sell_price, buy_take_profit, sell_take_profit, buy_stop_loss, sell_stop_loss
    except Exception as e:
        log_and_print(f"Error calculating levels: {e}")
        return None, None, None, None, None, None


def calculate_position_size(balance, risk_per_trade, stop_loss_pips, pip_value):
    try:
        position_size = (balance * risk_per_trade) / (stop_loss_pips * pip_value)
        return position_size
    except Exception as e:
        log_and_print(f"Error calculating position size: {e}")
        return 0.1


def manage_open_positions(symbol, params, volatility):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            raise ValueError(f"Failed to get positions for {symbol}")

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
                    place_order(symbol, position.volume, mt5.ORDER_TYPE_BUY, get_current_price(symbol)[1], get
                    current_price(symbol)[1] + params['take_profit'] * 0.0001, get
                    current_price(symbol)[1] - params['interval'] * 0.0001)
            except Exception as e:
            log_and_print(f"Error managing open positions for {symbol}: {e}")

    def update_trailing_stop_loss(symbol):
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                raise ValueError(f"Failed to get positions for {symbol}")

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
            log_and_print(f"Error updating trailing stop loss for {symbol}: {e}")

    def process_symbol(symbol, params):
        try:
            rates = get_1h_data(symbol)
            if rates is None:
                return

            close_prices = [rate['close'] for rate in rates]
            atr = talib.ATR(close_prices, timeperiod=14)[-1]  # ATR for volatility adjustment
            balance = mt5.account_info().balance
            position_size = calculate_position_size(balance, 0.01, 10, 10)

            manage_open_positions(symbol, params, atr)
            update_trailing_stop_loss(symbol)

            current_ask, current_bid = get_current_price(symbol)
            if current_ask is None or current_bid is None:
                return

            levels = calculate_levels(current_bid, current_ask, params['interval'], params['take_profit'], atr)
            market_trend = get_market_trend(symbol)

            if market_trend == "uptrend":
                place_order(symbol, position_size, mt5.ORDER_TYPE_BUY, levels[0], levels[2], levels[4])
            elif market_trend == "downtrend":
                place_order(symbol, position_size, mt5.ORDER_TYPE_SELL, levels[1], levels[3], levels[5])
        except Exception as e:
            log_and_print(f"Error processing symbol {symbol}: {e}")

    def main_loop(symbols):
        last_order_prices = {symbol: {'buy': None, 'sell': None} for symbol in symbols}

        while True:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(process_symbol, symbol, params) for symbol, params in symbols.items()]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        log_and_print(f"Error in processing symbol: {e}")

            # Sleep until the next full hour
            current_time = datetime.now()
            sleep_time = 3600 - (current_time.minute * 60 + current_time.second)
            log_and_print(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
