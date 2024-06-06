from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score
from sklearn.ensemble import VotingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import time
import threading
from data_collection import collect_and_preprocess_data

ensemble_model = None
scaler = StandardScaler()
model_trained_condition = threading.Condition()

def train_model():
    global ensemble_model, scaler
    while True:
        all_data = collect_and_preprocess_data()

        combined_data_list = []
        for symbol, symbol_data in all_data.items():
            if 'H1' not in symbol_data or symbol_data['H1'].empty:
                print(f"No H1 data for {symbol}")
                continue
            combined_symbol_data = symbol_data['H1'].copy()
            for tf_name, tf_data in symbol_data.items():
                if tf_name != 'H1':
                    for col in tf_data.columns:
                        combined_symbol_data[f"{col}_{tf_name}"] = tf_data[col]

            # Drop columns with more than 50% NaN values
            combined_symbol_data = combined_symbol_data.dropna(thresh=len(combined_symbol_data) // 2, axis=1)

            if not combined_symbol_data.empty:
                combined_data_list.append(combined_symbol_data)

        if not combined_data_list:
            print("No sufficient data to train the model.")
            time.sleep(3600)
            continue

        combined_data = pd.concat(combined_data_list)
        combined_data.dropna(inplace=True)  # Drop rows with NaN values

        if combined_data.empty:
            print("Combined data is empty after dropping NaN values.")
            time.sleep(3600)
            continue

        # Create features and target
        features = combined_data.columns.difference(['target'])
        X = combined_data[features]
        y = combined_data['target']

        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Train individual models
        lr = LogisticRegression(max_iter=1000)
        rf = RandomForestClassifier()
        xgb = XGBClassifier()
        lgbm = LGBMClassifier()

        # Create an ensemble of the models
        ensemble_model = VotingClassifier(estimators=[
            ('lr', lr),
            ('rf', rf),
            ('xgb', xgb),
            ('lgbm', lgbm)
        ], voting='hard')

        # Train the ensemble model
        ensemble_model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = ensemble_model.predict(X_test)
        print("Ensemble Model Accuracy:", accuracy_score(y_test, y_pred))

        # Notify trading thread that the model is trained
        with model_trained_condition:
            model_trained_condition.notify_all()

        # Retrain every hour
        time.sleep(3600)
