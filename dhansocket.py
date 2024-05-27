from dhanhq import dhanhq

client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

dhan = dhanhq(client_id, access_token)
print(dhan.get_holdings())


def get_historical_data(dhan, symbol, exchange, instrument_type, expiry, from_date, to_date):
    return dhan.historical_daily_data(
        symbol=symbol,
        exchange_segment=exchange,
        instrument_type=instrument_type,
        expiry_code=expiry,
        from_date=from_date,
        to_date=to_date
    )


# Corrected function call with proper argument names and values
historical_data = get_historical_data(
    dhan=dhan,
    symbol='NTPC',
    exchange=dhan.NSE,
    instrument_type="EQUITY",
    expiry=0,
    from_date='2022-01-08',
    to_date='2022-02-08'
)

print(historical_data)
