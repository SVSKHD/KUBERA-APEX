import pandas as pd
import pandas_ta as ta
import time
from pymongo import MongoClient
from dhanhq import dhanhq

# Initialize DhanHQ client
client_id = "1100567724"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzE5MTU1ODkzLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMDU2NzcyNCJ9.0cprkA0dIOG_j8ikgGWsMMKTrz0aKRC4axw6E6Jc_r4QpDGPJlJQfvK-G_snfjVeZ0a72C_LXs9ogKPbtmQbMQ";
dhan = dhanhq(client_id, access_token)

# Load the Excel file
security_df = pd.read_excel('./api-scrip-master.csv')
security_ids = security_df['SEM_SMST_SECURITY_ID'].tolist()

# Initialize MongoDB client
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["Kuberaapexdhan"]
trades_collection = db["trades"]
results_collection = db["results"]


def fetch_historical_data(security_id, start_date, end_date):
    data = dhan.historical_daily_data(
        symbol=security_id,
        exchange_segment=dhan.NSE,
        instrument_type='EQ',
        from_date=start_date,
        to_date=end_date
    )
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df


def calculate_metrics(df):
    df['daily_return'] = df['close'].pct_change()
    avg_daily_return = df['daily_return'].mean()
    volatility = df['daily_return'].std()
    sharpe_ratio = avg_daily_return / volatility
    return avg_daily_return, volatility, sharpe_ratio


def place_order(security_id, transaction_type, quantity):
    order = dhan.place_order(
        security_id=security_id,
        exchange_segment=dhan.NSE,
        transaction_type=transaction_type,
        quantity=quantity,
        order_type=dhan.MARKET,
        product_type=dhan.INTRA,
        price=0
    )
    return order


def save_trade_to_db(trade_details):
    trades_collection.insert_one(trade_details)


def backtest_strategy(security_id, df, target_return=0.05):
    df['signal'] = (df['daily_return'] > df['daily_return'].quantile(0.75)).astype(int)
    df['strategy_return'] = df['signal'].shift(1) * df['daily_return']
    cumulative_return = (1 + df['strategy_return']).cumprod() - 1
    profitable_days = (df['strategy_return'] > target_return).sum()
    return cumulative_return.iloc[-1], profitable_days


results = []
for security_id in security_ids:
    df = fetch_historical_data(security_id, '2023-01-01', '2023-12-31')
    avg_return, vol, sharpe = calculate_metrics(df)
    cumulative_return, profitable_days = backtest_strategy(security_id, df)
    result = {
        'security_id': security_id,
        'avg_return': avg_return,
        'volatility': vol,
        'sharpe_ratio': sharpe,
        'cumulative_return': cumulative_return,
        'profitable_days': profitable_days
    }
    results.append(result)
    results_collection.insert_one(result)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by='cumulative_return', ascending=False)

# Save results to a new Excel file
results_df.to_excel('profitable_symbols.xlsx', index=False)


# Continuous Monitoring and Trading
def analyze_patterns(df):
    df.ta.rsi(close='close', append=True)
    df.ta.macd(close='close', append=True)
    df['buy_signal'] = ((df['RSI_14'] < 30) & (df['MACD_12_26_9'] > df['MACDs_12_26_9'])).astype(int)
    df['sell_signal'] = ((df['RSI_14'] > 70) & (df['MACD_12_26_9'] < df['MACDs_12_26_9'])).astype(int)
    return df


while True:
    try:
        for security_id in security_ids:
            df = fetch_historical_data(security_id, '2024-01-01', '2024-12-31')
            df = analyze_patterns(df)

            if df['buy_signal'].iloc[-1]:
                trade_details = {
                    'security_id': security_id,
                    'transaction_type': 'BUY',
                    'quantity': 10,
                    'price': 0
                }
                place_order(security_id, 'BUY', 10)
                save_trade_to_db(trade_details)

            if df['sell_signal'].iloc[-1]:
                trade_details = {
                    'security_id': security_id,
                    'transaction_type': 'SELL',
                    'quantity': 10,
                    'price': 0
                }
                place_order(security_id, 'SELL', 10)
                save_trade_to_db(trade_details)

        time.sleep(60)  # Sleep for 1 minute before fetching new data
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)
