import pandas as pd

def calculate_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ma(data, period=20):
    return data['close'].rolling(window=period).mean()

def calculate_bollinger_bands(data, period=20, std_dev=2):
    ma = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper_band = ma + (std * std_dev)
    lower_band = ma - (std * std_dev)
    return upper_band, lower_band

def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    short_ema = data['close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['close'].ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal

def calculate_adx(data, period=14):
    high = data['high']
    low = data['low']
    close = data['close']

    plus_dm = high.diff()
    minus_dm = low.diff()

    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    plus_di = 100 * (plus_dm / atr).rolling(window=period).mean()
    minus_di = 100 * (minus_dm / atr).rolling(window=period).mean()
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(window=period).mean()

    return adx

def calculate_indicators(data):
    data['rsi'] = calculate_rsi(data)
    data['ma'] = calculate_ma(data)
    data['upper_band'], data['lower_band'] = calculate_bollinger_bands(data)
    data['macd'], data['macd_signal'] = calculate_macd(data)
    data['adx'] = calculate_adx(data)
    return data
