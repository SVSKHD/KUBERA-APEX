from dhanhq import dhanhq
import pandas as pd
import numpy as np

client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ"

dhan = dhanhq(client_id, access_token)

def get_historical_data(dhan, symbol, exchange, instrument_type, expiry, from_date, to_date):
    try:
        data = dhan.historical_daily_data(
            symbol=symbol,
            exchange_segment=exchange,
            instrument_type=instrument_type,
            expiry_code=expiry,
            from_date=from_date,
            to_date=to_date
        )
        if 'data' not in data or len(data['data']) == 0:
            raise ValueError(f"No data found for {symbol}")
        return data['data']
    except Exception as e:
        print(f"Error retrieving data for {symbol}: {e}")
        return None

def calculate_strategy(data):
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['Signal'] = np.where(data['SMA_50'] > data['SMA_200'], 1, 0)
    data['Position'] = data['Signal'].diff()
    return data

def backtest_strategy(data):
    data['Market Returns'] = np.log(data['close'] / data['close'].shift(1))
    data['Strategy Returns'] = data['Market Returns'] * data['Position'].shift(1)
    data['Cumulative Market Returns'] = data['Market Returns'].cumsum().apply(np.exp)
    data['Cumulative Strategy Returns'] = data['Strategy Returns'].cumsum().apply(np.exp)
    return data

def calculate_profit(data, initial_balance):
    data['Holdings'] = (data['Position'].shift(1) * initial_balance / data['close'].shift(1)).fillna(0)
    data['Cash'] = initial_balance - (data['Position'].cumsum() * data['close']).fillna(0)
    data['Portfolio Value'] = data['Holdings'] * data['close'] + data['Cash']
    data['Daily Profit'] = data['Portfolio Value'].diff().fillna(0)
    data['Cumulative Profit'] = data['Daily Profit'].cumsum()
    data['Profit Percentage'] = (data['Cumulative Profit'] / initial_balance) * 100
    data['Expected Profit'] = data['Daily Profit'].mean() * len(data)
    return data

def execute_trades(dhan, data, symbol):
    for i in range(1, len(data)):
        if data['Position'].iloc[i] == 1 and data['Position'].iloc[i - 1] == 0:
            print("Buy signal")
            # Buy signal
            # dhan.place_order(symbol=symbol, exchange=dhan.NSE, order_type='BUY', quantity=1, product_type='INTRADAY')
        elif data['Position'].iloc[i] == -1 and data['Position'].iloc[i - 1] == 1:
            print("Sell Signal")
            # Sell signal
            # dhan.place_order(symbol=symbol, exchange=dhan.NSE, order_type='SELL', quantity=1, product_type='INTRADAY')

def main():
    try:
        balance_limits = dhan.get_fund_limits()
        userInfoBalance = balance_limits['data']['availabelBalance']
        print("Available Balance:", userInfoBalance)
    except Exception as e:
        print(f"Error retrieving balance information: {e}")
        return

    initial_balance = userInfoBalance
    symbols = ['RELIANCE', 'TCS', 'INFY', 'NTPC']  # List of symbols to track
    from_date = '2024-05-01'
    to_date = '2024-05-31'
    results = []

    for symbol in symbols:
        historical_data = get_historical_data(
            dhan=dhan,
            symbol=symbol,
            exchange=dhan.NSE,
            instrument_type="EQUITY",
            expiry=0,
            from_date=from_date,
            to_date=to_date
        )

        if historical_data is None:
            continue

        df = pd.DataFrame(historical_data)

        print(f"Data for {symbol}:")
        print(df.head())  # Print first few rows to inspect the structure

        if 'Date' not in df.columns:
            if 'timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'])
            else:
                print(f"Neither 'Date' nor 'timestamp' column found in the historical data for {symbol}")
                continue

        df.set_index('Date', inplace=True)

        try:
            df = calculate_strategy(df)
            df = backtest_strategy(df)
            df = calculate_profit(df, initial_balance)
            results.append(df)
        except Exception as e:
            print(f"Error processing data for {symbol}: {e}")
            continue

        execute_trades(dhan, df, symbol)

    if results:
        combined_results = pd.concat(results)
        print(combined_results[['Portfolio Value', 'Cumulative Profit', 'Profit Percentage', 'Expected Profit']])
    else:
        print("No results to display")

if __name__ == "__main__":
    main()