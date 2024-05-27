import pandas as pd


def fetch_data_dhan(dhan, symbol, exchange_segment, instrument_type, from_date, to_date, expiry_code=0):
    data = dhan.historical_daily_data(
        symbol=symbol,
        exchange_segment=exchange_segment,
        instrument_type=instrument_type,
        expiry_code=expiry_code,
        from_date=from_date,
        to_date=to_date
    )

    df = pd.DataFrame(data['data'])
    if 'timestamp' in df.columns:
        df['date'] = pd.to_datetime(df['timestamp'])
        df.drop(columns=['timestamp'], inplace=True)
    else:
        print("The 'timestamp' column is not present in the data.")
    return df


def store_historical_data(db, dhan, symbols, exchange_segment, instrument_type, from_date, to_date):
    for symbol in symbols:
        df = fetch_data_dhan(dhan, symbol, exchange_segment, instrument_type, from_date, to_date)
        data = df.to_dict('records')
        for record in data:
            record['symbol'] = symbol
        db.historical_data.insert_many(data)


def fetch_latest_price(dhan, symbol, exchange_segment):
    data = dhan.historical_daily_data(symbol=symbol, exchange_segment=exchange_segment)
    latest_price = data['last_price']
    return latest_price
