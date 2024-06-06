from data_collection import initialize_mt5
from model_training import train_model
import trading_logic
import threading

# Initialize MetaTrader 5
initialize_mt5(login=212792645, password='pn^eNL4U', server='OctaFX-Demo')

# Start the training thread
training_thread = threading.Thread(target=train_model)
training_thread.start()

# Start the trading bot
trading_logic.run_trading_bot()
