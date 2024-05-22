import pandas as pd


def fetch_data_dhan(dhan, symbol, interval, days):
    data = dhan.get_historical_data(symbol=symbol, interval=interval, days=days)
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df
