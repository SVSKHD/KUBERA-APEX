import MetaTrader5 as mt5

# Your MT5 credentials and trading server
account_number = 212792645  # Replace with your real account number
password = 'pn^eNL4U'  # Replace with your real password
server = 'OctaFX-Demo'  # Replace with your MT5 server name

def connect_to_mt5(account_number, password, server):
    # Initialize MT5 connection
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False

    # Connect to the trading account
    authorized = mt5.login(account_number, password=password, server=server)
    if not authorized:
        print("login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    print("Connected to MT5 account #{}".format(account_number))
    return True

def get_account_balance():
    # Ensure we're connected to MT5
    if mt5.terminal_info() is None:
        print("Not connected to MT5.")
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info, error code =", mt5.last_error())
    else:
        print("Account Balance: ", account_info.balance)
