def identify_levels(data):
    support_level = data['low'].min()
    resistance_level = data['high'].max()
    return support_level, resistance_level

def generate_signal(data, current_price, support_level, resistance_level):
    ma = data['ma'].iloc[-1]
    rsi = data['rsi'].iloc[-1]
    upper_band = data['upper_band'].iloc[-1]
    lower_band = data['lower_band'].iloc[-1]
    macd = data['macd'].iloc[-1]
    macd_signal = data['macd_signal'].iloc[-1]
    adx = data['adx'].iloc[-1]

    trend_strength = adx > 25  # Consider a trend strong if ADX is above 25

    if current_price > resistance_level and rsi < 70 and current_price > ma and current_price < upper_band and macd > macd_signal and trend_strength:
        return "BUY"
    elif current_price < support_level and rsi > 30 and current_price < ma and current_price > lower_band and macd < macd_signal and trend_strength:
        return "SELL"
    else:
        return "HOLD"
