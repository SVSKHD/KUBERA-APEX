import MetaTrader5 as mt5
from connection import initialize_mt5

def get_currency_symbols():
    symbols = mt5.symbols_get()
    filtered_symbols = [s.name for s in symbols if any(base in s.name for base in ["USD", "EUR", "JPY", "AUD"])]
    return filtered_symbols

if __name__ == "__main__":
    login = 212792645
    password = 'pn^eNL4U'
    server = 'OctaFX-Demo'

    if initialize_mt5(login, password, server):
        currency_symbols = get_currency_symbols()
        print(f"Available currency symbols: {currency_symbols}")
        mt5.shutdown()
