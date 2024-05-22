from sklearn.ensemble import RandomForestClassifier
import pandas as pd


# Train a machine learning model
def train_model(data):
    # Feature engineering
    data['rsi'] = calculate_rsi(data)
    data['ma'] = calculate_ma(data)
    data['upper_band'], data['lower_band'] = calculate_bollinger_bands(data)
    data['macd'], data['macd_signal'] = calculate_macd(data)
    data['adx'] = calculate_adx(data)

    # Create feature set
    features = data[['rsi', 'ma', 'macd', 'macd_signal', 'adx']]
    target = (data['close'].shift(-1) > data['close']).astype(int)  # 1 if next close price is higher, else 0

    # Split data into training and test sets
    train_size = int(len(features) * 0.8)
    X_train, X_test = features[:train_size], features[train_size:]
    y_train, y_test = target[:train_size], target[train_size:]

    # Train the model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    return model


# Predict using the trained model
def model_predict(data, model):
    features = data[['rsi', 'ma', 'macd', 'macd_signal', 'adx']].iloc[-1:]
    prediction = model.predict(features)

    if prediction == 1:
        return "BUY"
    else:
        return "SELL"
