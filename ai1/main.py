import time
import logging
from datetime import datetime
from mt5_init import initialize_mt5, shutdown_mt5
from trading_logic import manage_open_positions, update_trailing_stop_loss, log_and_print
from trend_analysis import trade

# Configure logging
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define symbols and their parameters
symbols = {
    'EURUSD': {'interval': 15, 'take_profit': 45},
    'GBPUSD': {'interval': 15, 'take_profit': 45}
}


def main_loop():
    last_order_prices = {symbol: {'buy': None, 'sell': None} for symbol in symbols}

    while True:
        for symbol, params in symbols.items():
            trade(symbol, params)
            manage_open_positions(symbol, params)
            update_trailing_stop_loss(symbol)

        # Sleep until the next full hour
        current_time = datetime.now()
        sleep_time = 3600 - (current_time.minute * 60 + current_time.second)
        log_and_print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    initialize_mt5(login="your_login", password="your_password", server="your_server")
    try:
        main_loop()
    finally:
        shutdown_mt5()
