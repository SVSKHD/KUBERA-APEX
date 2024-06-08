import datetime
from live_feed import run_live_feed, is_market_open
from historical_analysis import run_historical_analysis

# Function to check if today is a weekday
def is_weekday():
    today = datetime.datetime.today().weekday()
    return today < 5  # 0 is Monday, 4 is Friday

# Main execution logic
if __name__ == "__main__":
    if is_weekday() and is_market_open():
        run_live_feed()
    else:
        run_historical_analysis()
