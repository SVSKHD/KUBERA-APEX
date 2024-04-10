import MetaTrader5 as mt5
import time
from startup import connect_to_mt5, get_account_balance
from trade_logic import check_price_difference

account_number = 212792645  # Your account number
password = 'pn^eNL4U'  # Your password
server = 'OctaFX-Demo'  # Your server
symbol = 'EURUSD'  # Symbol to observe


def main():
    if connect_to_mt5(account_number, password, server):
        get_account_balance()
        try:
            while True:
                check_price_difference(symbol)
                time.sleep(60)
        except KeyboardInterrupt:
            print("\nScript interrupted by user.")
        finally:
            mt5.shutdown()
            print("MT5 connection closed.")
    else:
        print("Failed to connect to MetaTrader 5.")


if __name__ == "__main__":
    main()
