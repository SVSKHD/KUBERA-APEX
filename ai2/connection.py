import MetaTrader5 as mt5


def initialize_mt5(account, password, server):
    if not mt5.initialize():
        print("initialize() failed")
        mt5.shutdown()
        return False

    if not mt5.login(account, password, server):
        print("login() failed")
        mt5.shutdown()
        return False

    return True


def shutdown_mt5():
    mt5.shutdown()
