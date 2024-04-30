import MetaTrader5 as mt5
import time
import math
import pytz
from datetime import datetime, timedelta
import asyncio


def daily_trading_recommendations():
    today = datetime.now()  # Now you can call datetime.now() directly
    weekday = today.weekday()  # Monday is 0 and Sunday is 6

    # Define trading pairs for weekends and weekdays
    weekend_pairs = ['BTCUSD']
    weekday_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']

    # Check if today is Saturday or Sunday
    if weekday in [5, 6]:  # 5 is Saturday, 6 is Sunday
        return f"Today is {'Saturday' if weekday == 5 else 'Sunday'}. Recommended trading pair: {', '.join(weekend_pairs)}"
    else:
        day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][weekday]
        return f"Today is {day_name}. Recommended trading pairs: {', '.join(weekday_pairs)}"


# get account balance
def get_account_balance():
    if mt5.terminal_info() is None:
        print("S.py : Not connected to MT5.")
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("S.py : Failed to get account info, error code =", mt5.last_error())
    else:
        print("S.py :  Account Balance: ", account_info.balance)


# start the connection between meta trader5 and app
def connect_to_mt5(account_number, password, server):
    # Initialize MT5 connection
    if not mt5.initialize():
        print("S.py : initialize() failed, error code =", mt5.last_error())
        return False

    # Connect to the trading account
    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("S.py : login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    print("reusables.py : Connected to MT5 account #{}".format(account_number))
    return True


def adjust_volume(volume, symbol_info):
    min_volume = symbol_info.volume_min
    step = symbol_info.volume_step
    volume = max(min_volume, volume)  # Ensure volume is at least the minimum
    # Adjust volume to the nearest step multiple above the minimum
    volume = ((int((volume - min_volume) / step) + 1) * step) + min_volume if volume % step != 0 else volume
    return volume


def adjust_price(price, symbol_info):
    point = symbol_info.point
    price_scale = round(-math.log10(point))
    return round(price, price_scale)


# fetch-candels ---------------------------------------------------------------------------------------------------------------------------------Section>

async def fetch_bars_async(symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
    return await asyncio.to_thread(fetch_bars, symbol, timeframe, count)


def fetch_bars(symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
    # Initialize and select the symbol
    if not mt5.initialize():
        print("Failed to initialize MT5, error code =", mt5.last_error())
        return None

    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol {symbol}.")
        return None

    # Define timezone to UTC
    timezone = pytz.utc

    # Fetch the latest bar time from MT5
    recent_bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    if recent_bars is None or len(recent_bars) == 0:
        print(f"Failed to fetch recent bar for {symbol}. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return None

    # Calculate the date range for fetching historical data
    utc_to = datetime.fromtimestamp(recent_bars[0]['time'], tz=timezone)
    utc_from = utc_to - timedelta(hours=count)

    # Ensure that datetime objects are localized to UTC
    if utc_from.tzinfo is None or utc_to.tzinfo is None:
        utc_from = timezone.localize(utc_from)
        utc_to = timezone.localize(utc_to)

    # Fetch the historical bars
    bars = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    if bars is None or len(bars) == 0:
        print(f"Failed to fetch bars for {symbol}. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return None

    # Format the fetched data
    bars_data = [{
        'time': datetime.fromtimestamp(bar['time'], tz=timezone).strftime('%Y-%m-%d %H:%M:%S'),
        'open': bar['open'],
        'high': bar['high'],
        'low': bar['low'],
        'close': bar['close'],
        'volume': bar['tick_volume']
    } for bar in bars]

    # Clean up the connection

    return bars_data


# Trade Methods ---------------------------------------------------------------------------------------------------------------------------------Section>


def is_hammer(candle):
    # Define the criteria for a hammer
    body = abs(candle['close'] - candle['open'])
    candle_range = candle['high'] - candle['low']
    lower_wick = min(candle['close'], candle['open']) - candle['low']
    upper_wick = candle['high'] - max(candle['close'], candle['open'])

    # Hammer: small body, long lower wick, very small or no upper wick
    return body <= candle_range * 0.3 and lower_wick >= body * 2 and upper_wick <= body * 0.5


def is_morning_star(bars):
    if len(bars) < 3:
        return False

    candle1, candle2, candle3 = bars[-3], bars[-2], bars[-1]
    if candle1['close'] < candle1['open'] and candle3['close'] > candle3['open']:
        if candle2['close'] < candle1['close'] and candle3['close'] > candle2['close'] and candle3['close'] > candle1[
            'open']:
            return True
    return False


def is_evening_star(bars):
    if len(bars) < 3:
        return False

    candle1, candle2, candle3 = bars[-3], bars[-2], bars[-1]
    if candle1['close'] > candle1['open'] and candle3['close'] < candle3['open']:
        if candle2['close'] > candle1['close'] and candle3['close'] < candle2['close'] and candle3['close'] < candle1[
            'open']:
            return True
    return False


def is_engulfing(candle1, candle2):
    """
    Determine if the relationship between two consecutive candles forms an engulfing pattern.

    Args:
        candle1 (dict): The first candle with 'open', 'close', 'high', and 'low'.
        candle2 (dict): The second candle with 'open', 'close', 'high', and 'low'.

    Returns:
        str: 'BULLISH' if a bullish engulfing pattern is found, 'BEARISH' if a bearish engulfing pattern is found,
             'NONE' if no engulfing pattern is detected.
    """
    # Check for bullish engulfing:
    # Candle1 is bearish and Candle2 is bullish and Candle2 engulfs Candle1
    if candle1['open'] > candle1['close'] and candle2['open'] < candle2['close']:
        if candle2['open'] <= candle1['close'] and candle2['close'] >= candle1['open']:
            return 'BULLISH'

    # Check for bearish engulfing:
    # Candle1 is bullish and Candle2 is bearish and Candle2 engulfs Candle1
    elif candle1['open'] < candle1['close'] and candle2['open'] > candle2['close']:
        if candle2['open'] >= candle1['open'] and candle2['close'] <= candle1['close']:
            return 'BEARISH'

    return 'NONE'


def is_piercing_line(bars):
    if len(bars) < 2:
        return False

    candle1, candle2 = bars[-2], bars[-1]
    if candle1['open'] > candle1['close'] and candle2['open'] < candle1['low'] and candle2['close'] > (
            candle1['open'] + candle1['close']) / 2:
        return True
    return False


def is_dark_cloud_cover(bars):
    if len(bars) < 2:
        return False

    candle1, candle2 = bars[-2], bars[-1]
    if candle1['open'] < candle1['close'] and candle2['open'] > candle1['high'] and candle2['close'] < (
            candle1['open'] + candle1['close']) / 2:
        return True
    return False


def is_doji(bar):
    body = abs(bar['close'] - bar['open'])
    candle_range = bar['high'] - bar['low']
    return body <= candle_range * 0.1


def analyze_market_trend(bars):
    bullish_signals = 0
    bearish_signals = 0

    # Check for Doji
    if len(bars) > 0 and is_doji(bars[-1]):
        # If Doji is found, check the next candle for confirmation if it exists
        if len(bars) > 1:
            next_candle_trend = is_engulfing(bars[-2], bars[-1])
            if next_candle_trend == 'BULLISH':
                bullish_signals += 1
            elif next_candle_trend == 'BEARISH':
                bearish_signals += 1

    # Check for Engulfing pattern
    if len(bars) > 1:
        engulfing_trend = is_engulfing(bars[-2], bars[-1])
        if engulfing_trend == 'BULLISH':
            bullish_signals += 1
        elif engulfing_trend == 'BEARISH':
            bearish_signals += 1

    # Check for Morning Star and Evening Star
    if len(bars) >= 3:
        if is_morning_star(bars[-3:]):
            bullish_signals += 1
        if is_evening_star(bars[-3:]):
            bearish_signals += 1

    # Check for Piercing Line and Dark Cloud Cover
    if len(bars) > 1:
        if is_piercing_line(bars[-2:]):
            bullish_signals += 1
        if is_dark_cloud_cover(bars[-2:]):
            bearish_signals += 1

    total_signals = bullish_signals + bearish_signals

    # Determine the suggested trend and confidence level
    if total_signals == 0:
        suggested_trend = 'UNCERTAIN'
        confidence = 0
    elif bullish_signals > bearish_signals:
        suggested_trend = 'BULLISH'
        confidence = (bullish_signals / total_signals) * 100
    else:
        suggested_trend = 'BEARISH'
        confidence = (bearish_signals / total_signals) * 100

    return {'trend': suggested_trend, 'confidence': confidence}


def analyze_and_trade(symbol, bars):
    analysis = analyze_market_trend(bars)
    trend = analysis['trend']
    confidence = analysis['confidence']

    if trend == 'UNCERTAIN' or confidence < 50:  # Assuming 50% as a threshold for confidence
        print(f"Market trend is uncertain or confidence is too low ({confidence}%), no trade initiated.")
        return

    print(f"Detected {trend} trend with {confidence}% confidence.")
    # Ensure the symbol is available in MT5
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}, symbol not found on MT5.")
        return

    # Get current price for the symbol
    current_price = mt5.symbol_info_tick(symbol).ask if trend == 'BULLISH' else mt5.symbol_info_tick(symbol).bid
    initial_price = current_price
    volume = 0.1  # Example volume
    order_type = 'BUY' if trend == 'BULLISH' else 'SELL'
    order_sent = False
    try:
        while True:
            current_tick = mt5.symbol_info_tick(symbol)
            current_price = current_tick.ask if order_type == 'BUY' else current_tick.bid
            pip_scale = 0.0001 if 'JPY' not in symbol else 0.01
            price_difference = (current_price - initial_price) / pip_scale

            # Check if the price has moved 15 pips in the direction of the trend before placing a trade
            if not order_sent and ((order_type == 'BUY' and price_difference >= 15) or (
                    order_type == 'SELL' and price_difference <= -15)):
                result = order_send(symbol, order_type, volume, current_price)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"Trade placed: {order_type} at {current_price}.")
                    order_sent = True
                    initial_price = current_price  # Update initial price to the price at which trade was executed
                else:
                    print("Failed to place trade.")
                    break

            # Check for opposite movement of 10 pips to close the trade
            if order_sent:
                loss_difference = (current_price - initial_price) / pip_scale
                if (order_type == 'BUY' and loss_difference <= -10) or (order_type == 'SELL' and loss_difference >= 10):
                    print("Market moved 10 pips against the position, closing trade.")
                    close_all_trades()
                    break

            time.sleep(1)  # Delay to limit the frequency of API calls

    except Exception as e:
        print(f"Error during trading: {e}")
    finally:
        mt5.shutdown()

    return


# buy or close orders
def order_send(symbol, order_type, volume, price=None, slippage=2, magic=0, comment=""):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Failed to find symbol, order send failed.")
        return None

    if order_type == 'BUY':
        order_type_mt5 = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask if price is None else price
    elif order_type == 'SELL':
        order_type_mt5 = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid if price is None else price
    else:
        print("Invalid order type.")
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
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order send failed, retcode={result.retcode}")
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


# Price Handling ---------------------------------------------------------------------------------------------------------------------------------Section>
# Get the live price of a currency pair
def get_live_price(symbol):
    # Check if the symbol exists in MT5
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} not found, can't get price.")
        return None

    # Get tick data
    tick = mt5.symbol_info_tick(symbol)
    return tick.ask  # You can change to tick.bid based on your requirement


# Observe price and check for 15 pip difference


def observe_price(symbol, pip_diff=15, volume=0.1, stop_loss_pips=10):
    # Ensure the symbol is available in MT5
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}, symbol not found on MT5.")
        mt5.shutdown()
        return

    # Get the initial tick data for real-time analysis
    initial_tick = mt5.symbol_info_tick(symbol)
    if initial_tick is None:
        print("Failed to get tick data for", symbol)
        mt5.shutdown()
        return
    last_traded_price = initial_tick.ask  # Start with the current ask price

    print(f"Starting observation for {symbol} at price: {last_traded_price}")

    order_type = None

    try:
        while True:
            current_tick = mt5.symbol_info_tick(symbol)
            if current_tick is None:
                continue  # Skip this iteration if tick data is not available

            current_price = current_tick.ask
            pip_scale = 0.0001 if not symbol.endswith("JPY") else 0.01
            difference = (current_price - last_traded_price) / pip_scale

            # Check if the price has moved 15 pips away from the last traded price
            if abs(difference) >= pip_diff:
                direction = "increased" if difference > 0 else "decreased"
                print(
                    f"{pip_diff} pip {direction} reached for {symbol} at price: {current_price} ({difference:+.2f} pips)")
                close_all_trades()
                order_type = 'BUY' if direction == "increased" else 'SELL'
                order_send(symbol, order_type, volume)  # Execute the trade
                last_traded_price = current_price  # Update the last traded price to current
                print(f"New base price for next trade: {last_traded_price}")

            # Monitoring for stop loss condition
            loss_difference = (current_price - last_traded_price) / pip_scale
            if (order_type == 'BUY' and loss_difference <= -stop_loss_pips) or (
                    order_type == 'SELL' and loss_difference >= stop_loss_pips):
                print(f"Market moved {stop_loss_pips} pips against the position; closing all trades.")
                close_all_trades()  # Close all trades if the market moves 10 pips against the trade
                break  # Optional: stop the function after closing trades to reassess strategy

            time.sleep(1)  # Small delay to prevent excessive CPU usage
    finally:
        mt5.shutdown()


# Manage trades based on signals
def manage_trades(symbol, signal, max_trades=4, minimal_profit=0.0001):
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None and mt5.last_error()[0] != 1:  # No positions error code
            print("Failed to get positions for", symbol)
            return

        current_trades = len(positions)
        if positions and (signal == 'buy' and positions[0].type == mt5.ORDER_TYPE_SELL) or \
                (signal == 'sell' and positions[0].type == mt5.ORDER_TYPE_BUY):
            for pos in positions:
                close_position(pos, minimal_profit)

        if current_trades < max_trades:
            order_send(symbol, signal.upper(), 0.01)  # Example: 0.01 lots

    finally:
        mt5.shutdown()


# Close position with minimal profit check
def close_position(position, minimal_profit):
    current_price = mt5.symbol_info_tick(
        position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
    if (position.type == mt5.ORDER_TYPE_BUY and (current_price - position.price) > minimal_profit) or \
            (position.type == mt5.ORDER_TYPE_SELL and (position.price - current_price) > minimal_profit):
        order_send(position.symbol, 'SELL' if position.type == mt5.ORDER_TYPE_BUY else 'BUY', position.volume,
                   current_price)
