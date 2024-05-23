def generate_signal(data, current_price):
    ma = data['ma'].iloc[-1]
    rsi = data['rsi'].iloc[-1]
    macd = data['macd'].iloc[-1]
    macd_signal = data['macd_signal'].iloc[-1]
    adx = data['adx'].iloc[-1]

    trend_strength = adx > 25  # Consider a trend strong if ADX is above 25

    if rsi < 30 and current_price > ma and macd > macd_signal and trend_strength:
        return "BUY"
    elif rsi > 70 and current_price < ma and macd < macd_signal and trend_strength:
        return "SELL"
    else:
        return "HOLD"

def generate_multitimeframe_signal(multi_data, current_price):
    signals = []
    for timeframe, data in multi_data.items():
        data = calculate_indicators(data)
        signal = generate_signal(data, current_price)
        signals.append(signal)

    if all(signal == "BUY" for signal in signals):
        return "BUY"
    elif all(signal == "SELL" for signal in signals):
        return "SELL"
    else:
        return "HOLD"
