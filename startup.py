import MetaTrader5 as mt5
from risk_management import close_all_trades

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
    if mt5.terminal_info() is None:
        print("Not connected to MT5.")
        return

    # Get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info, error code =", mt5.last_error())
    else:
        print("Account Balance: ", account_info.balance)


def calculate_open_trades_profit_loss_percentages_and_close():
    if not mt5.terminal_info():
        print("Not connected to MT5.")
        return

    # Get the current open trades
    open_trades = mt5.positions_get()
    if open_trades is None or len(open_trades) == 0:
        print("No open trades or failed to retrieve trades, error code =", mt5.last_error())
        return

    total_profit = sum(trade.profit for trade in open_trades if trade.profit > 0)
    total_loss = -sum(trade.profit for trade in open_trades if trade.profit < 0)

    # Get account info for total capital
    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info, error code =", mt5.last_error())
        return
    total_capital = account_info.balance

    # Calculate percentages
    profit_percentage = (total_profit / total_capital) * 100
    loss_percentage = (total_loss / total_capital) * 100

    print(f"Open Trades Profit Percentage: {profit_percentage:.2f}%")
    print(f"Open Trades Loss Percentage: {loss_percentage:.2f}%")

    # Check if conditions to close all trades are met
    if profit_percentage >= 2 or loss_percentage >= 1:
        print("Conditions met to close all trades. Proceeding to close...")
        close_all_trades()
