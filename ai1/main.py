import time
import logging
from datetime import datetime
from mt5_init import initialize_mt5, shutdown_mt5
from trading_logic import main_loop
from config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER

# Configure logging
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define symbols and their parameters
symbols = {
    'EURUSD': {'interval': 15, 'take_profit': 45},
    'GBPUSD': {'interval': 15, 'take_profit': 45}
}

if __name__ == "__main__":
    initialize_mt5(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER)
    try:
        main_loop(symbols)
    finally:
        shutdown_mt5()
