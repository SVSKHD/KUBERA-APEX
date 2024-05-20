import MetaTrader5 as mt5


def initialize_mt5(login, password, server):
    if not mt5.initialize(login=login, password=password, server=server):
        print("MetaTrader5 initialization failed")
        mt5.shutdown()
        exit()


def shutdown_mt5():
    mt5.shutdown()
