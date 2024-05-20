import MetaTrader5 as mt5
from trading_logic import get_current_price, calculate_position_size, calculate_levels
from reusable import log_and_print, place_order
import talib


def get_market_condition(symbol):
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None:
            log_and_print(f"Failed to get rates for {symbol}")
            return None

        close_prices = [rate['close'] for rate in rates]
        high_prices = [rate['high'] for rate in rates]
        low_prices = [rate['low'] for rate in rates]

        if len(close_prices) < 100:
            return None

        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)
        stddev = talib.STDDEV(close_prices, timeperiod=14, nbdev=1)

        if stddev[-1] > atr[-1]:
            return "trending"
        else:
            return "ranging"
    except Exception as e:
        log_and_print(f"Error determining market condition: {e}")
        return None


def get_market_trend(symbol):
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None:
            log_and_print(f"Failed to get rates for {symbol}")
            return None

        close_prices = [rate['close'] for rate in rates]
        high_prices = [rate['high'] for rate in rates]
        low_prices = [rate['low'] for rate in rates]

        if len(close_prices) < 100:
            return None

        ema_50 = talib.EMA(close_prices, timeperiod=50)
        ema_200 = talib.EMA(close_prices, timeperiod=200)

        if ema_50[-1] > ema_200[-1]:
            return "uptrend"
        elif ema_50[-1] < ema_200[-1]:
            return "downtrend"
        else:
            return "sideways"
    except Exception as e:
        log_and_print(f"Error determining market trend: {e}")
        return None


def trade(symbol, params):
    try:
        market_condition = get_market_condition(symbol)
        market_trend = get_market_trend(symbol)

        if market_condition == "ranging":
            log_and_print("Market is ranging. No trades will be placed.")
            return

        current_ask, current_bid = get_current_price(symbol)
        if current_ask is None or current_bid is None:
            return

        position_size = calculate_position_size()
        levels = calculate_levels(current_bid, current_ask, params['interval'], params['take_profit'])

        if market_trend == "uptrend":
            place_order(symbol, position_size, mt5.ORDER_TYPE_BUY, levels[0], levels[2], levels[4])
        elif market_trend == "downtrend":
            place_order(symbol, position_size, mt5.ORDER_TYPE_SELL, levels[1], levels[3], levels[5])
    except Exception as e:
        log_and_print(f"Error executing trade: {e}")
