import pandas as pd
from dhanhq import dhanhq
from datetime import datetime

# Initialize the Dhan API client
client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

dhan = dhanhq(client_id, access_token)

# Read the CSV file to get the list of symbols
file_path = 'api-scrip-master.csv'
symbols_df = pd.read_csv(file_path, dtype=str, low_memory=False)

# Print column names to ensure correct column is used
print("CSV Columns:", symbols_df.columns)


# Function to fetch the latest price (LTP) for a symbol using intraday minute data
def get_latest_price(symbol_id, exchange_segment='NSE_EQ', instrument_type='EQUITY'):
    try:
        data = dhan.intraday_minute_data(
            security_id=symbol_id,
            exchange_segment=exchange_segment,
            instrument_type=instrument_type
        )
        if data and 'data' in data and data['data']:
            latest_price = data['data'][-1]['close']  # 'close' is the closing price of the most recent minute
            return latest_price
        else:
            print(f"No data found for symbol {symbol_id}. Market might be closed.")
            return None
    except Exception as e:
        print(f"Error fetching latest price for symbol {symbol_id}: {e}")
        return None


# Scan and store prices for all symbols
def scan_all_prices(symbols_df):
    prices = {}
    for index, row in symbols_df.iterrows():
        symbol_id = row['SEM_SMST_SECURITY_ID']  # Ensure the correct column name is used
        price = get_latest_price(symbol_id)
        if price is not None:
            prices[symbol_id] = price
    return prices


if __name__ == "__main__":
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Scanning prices at: {current_time}")

    prices = scan_all_prices(symbols_df)
    if not prices:
        print("Market is closed. Please come back when the market is open.")
    else:
        for symbol_id, price in prices.items():
            print(f"The latest price for {symbol_id} is: {price}")
