import datetime
#
#
# def get_today():
#     today = datetime.datetime.now()
#     day_name = today.strftime("%A")
#     day_number = int(today.strftime("%d"))
#     weekday_number = today.isoweekday()
#
#     return day_name, day_number, weekday_number
#
#
# def print_currency_pairs():
#     day_name, day_number, weekday_config = get_today()
#
#     # Check if today is Saturday or Sunday
#     if weekday_config in [6, 7]:  # Adjusted to Saturday (6) or Sunday (7)
#         pairs = "BTCUSD, ETHUSD"
#     else:
#         pairs = "EURUSD, GBPUSD, USDJPY"
#
#     print(f"Today is {day_name}, the {day_number}th (Day {weekday_config} of the week). Trading pairs: {pairs}")
#
#
# # Example usage
# print_currency_pairs()


# import MetaTrader5 as mt5
# from datetime import datetime, timedelta
#
#
# def fetch_bars(symbol, timeframe=mt5.TIMEFRAME_H1, n_bars=100):
#     # Initialize MT5 connection if necessary
#     if not mt5.initialize():
#         print("initialize() failed, error code =", mt5.last_error())
#         mt5.shutdown()
#         return None
#
#     # Set the timeframe and number of bars to fetch
#     utc_from = datetime.now() - timedelta(weeks=2)  # For example, last two weeks
#     rates = mt5.copy_rates_from(symbol, timeframe, utc_from, n_bars)
#
#     mt5.shutdown()
#
#     if rates is None:
#         print("No rates retrieved, error code =", mt5.last_error())
#         return None
#
#     # Convert to list of dictionaries for easier handling
#     bars = [{'time': rate['time'], 'open': rate['open'], 'high': rate['high'],
#              'low': rate['low'], 'close': rate['close'], 'volume': rate['tick_volume']}
#             for rate in rates]
#
#     return bars
#
# bars = fetch_bars("BTCUSD")

def get_today():
    today = datetime.datetime.now()
    day_name = today.strftime("%A")
    day_number = int(today.strftime("%d"))
    weekday_number = today.isoweekday()

    print(day_name , day_number)
    return day_name, day_number, weekday_number

get_today()