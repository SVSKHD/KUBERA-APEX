import datetime


def get_today():
    today = datetime.datetime.now()
    day_name = today.strftime("%A")
    day_number = int(today.strftime("%d"))
    weekday_number = today.isoweekday()

    return day_name, day_number, weekday_number


def print_currency_pairs():
    day_name, day_number, weekday_config = get_today()

    # Check if today is Saturday or Sunday
    if weekday_config in [6, 7]:  # Adjusted to Saturday (6) or Sunday (7)
        pairs = "BTCUSD, ETHUSD"
    else:
        pairs = "EURUSD, GBPUSD, USDJPY"

    print(f"Today is {day_name}, the {day_number}th (Day {weekday_config} of the week). Trading pairs: {pairs}")


# Example usage
print_currency_pairs()
