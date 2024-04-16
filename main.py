import MetaTrader5 as mt5
import time
import threading
import datetime  # Added to check the day of the week
from startup import connect_to_mt5, get_account_balance , calculate_open_trades_profit_loss_percentages_and_close
from trade_logic import check_price_difference

# Define your account details
account_number = 212792645  # Your account number
password = 'pn^eNL4U'  # Your password
server = 'OctaFX-Demo'  # Your server

# Symbols for trading on weekdays and weekends
weekday_symbols = ['EURUSD', 'GBPUSD']  # Typical Forex currencies
weekend_symbols = ['BTCUSD', 'ETHUSD']  # Major cryptocurrencies


def trade_currency(symbol):
    if connect_to_mt5(account_number, password, server):
        get_account_balance()
        try:
            while True:
                check_price_difference(symbol)
                calculate_open_trades_profit_loss_percentages_and_close()
                time.sleep(1)  # You might adjust the sleep time based on your trading strategy
        except KeyboardInterrupt:
            print(f"main.py :  \nScript interrupted by user for {symbol}.")
        finally:
            print(f"main.py : MT5 connection closed for {symbol}.")
    else:
        print(f"main.py : Failed to connect to MetaTrader 5 for {symbol}.")


def main():
    today = datetime.datetime.now().weekday()
    if today >= 5:  # If it's Saturday (5) or Sunday (6)
        symbols = weekend_symbols
    else:
        symbols = weekday_symbols
    threads = []
    for symbol in symbols:
        # Create a thread for each symbol
        thread = threading.Thread(target=trade_currency, args=(symbol,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
