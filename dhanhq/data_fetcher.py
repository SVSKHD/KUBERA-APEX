import pandas as pd


def fetch_data_dhan(dhan, symbol, interval, days, is_option=False, strike_price=None, option_type=None,
                    expiry_date=None):
    if is_option:
        # Fetch options data (this is a placeholder, replace with actual API call)
        data = dhan.get_option_data(symbol=symbol, interval=interval, days=days, strike_price=strike_price,
                                    option_type=option_type, expiry_date=expiry_date)
    else:
        # Fetch equities data
        data = dhan.get_historical_data(symbol=symbol, interval=interval, days=days)

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def fetch_tradable_instruments(dhan):
    # Fetch all tradable instruments (this is a placeholder, replace with actual API call)
    instruments = dhan.get_all_tradable_instruments()
    return instruments
