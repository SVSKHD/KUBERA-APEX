import MetaTrader5 as mt5
def initialize_mt5(login, password, server):
    if not mt5.initialize(login=login, password=password, server=server):
        print("MT5 initialization failed, error code =", mt5.last_error())
        return False
    else:
        print("Connected and ready to take off")
    return True