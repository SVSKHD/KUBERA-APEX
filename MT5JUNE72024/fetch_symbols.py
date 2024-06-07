import MetaTrader5 as mt5

def get_currency_symbols():
    symbols = mt5.symbols_get()
    filtered_symbols = [s.name for s in symbols if any(base in s.name for base in ["USD", "EUR", "JPY", "AUD"])]
    return filtered_symbols
