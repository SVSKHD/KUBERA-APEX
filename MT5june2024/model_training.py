from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import VotingClassifier
from sklearn.preprocessing import StandardScaler
import pandas as pd
import time
import threading
from data_collection import collect_and_preprocess_data
import matplotlib.pyplot as plt
import os

ensemble_model = None
scaler = StandardScaler()
model_trained_condition = threading.Condition()

def analyze_data_distribution(data):
    # Plot the distribution of the target variable
    plt.figure(figsize=(10, 6))
    data['target'].value_counts().plot(kind='bar')
    plt.title('Distribution of Target Variable')
    plt.xlabel('Target')
    plt.ylabel('Count')
    plt.savefig('plots/target_distribution.png')
    plt.close()

    # Plot the distribution of each feature
    features = data.columns.difference(['target'])
    for feature in features:
        plt.figure(figsize=(10, 6))
        data[feature].hist(bins=50)
        plt.title(f'Distribution of {feature}')
        plt.xlabel(feature)
        plt.ylabel('Frequency')
        plt.savefig(f'plots/{feature}_distribution.png')
        plt.close()

def train_model():
    global ensemble_model, scaler
    while True:
        print("Starting model training...")
        all_data = collect_and_preprocess_data()
        print("Data collected and preprocessed.")

        combined_data_list = []
        for symbol, symbol_data in all_data.items():
            print(f"Processing symbol: {symbol}")
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

        # Create directories for saving plots if not exist
        os.makedirs('plots', exist_ok=True)

        # Analyze data distribution
        analyze_data_distribution(combined_data)

        # Create features and target
        features = combined_data.columns.difference(['target'])
        X = combined_data[features]
        y = combined_data['target']

        # Scale the data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split the data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

        # Train individual models with regularization
        lr = LogisticRegression(max_iter=1000, C=0.1)  # Added regularization
        rf = RandomForestClassifier(n_estimators=100, max_depth=10)  # Limited depth to prevent overfitting
        xgb = XGBClassifier()
        lgbm = LGBMClassifier()

        # Create an ensemble of the models
        ensemble_model = VotingClassifier(estimators=[
            ('lr', lr),
            ('rf', rf),
            ('xgb', xgb),
            ('lgbm', lgbm)
        ], voting='hard')

        # Cross-validation
        scores = cross_val_score(ensemble_model, X_train, y_train, cv=5)
        print(f"Cross-Validation Scores: {scores}")
        print(f"Mean Cross-Validation Score: {scores.mean()}")

        # Train the ensemble model
        ensemble_model.fit(X_train, y_train)

        # Evaluate the model on the test set
        y_test_pred = ensemble_model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        print(f"Test Accuracy: {test_accuracy}")
        print(classification_report(y_test, y_test_pred))

        # Notify trading thread that the model is trained
        with model_trained_condition:
            model_trained_condition.notify_all()
            print("Model training completed and condition notified.")

        # Retrain every hour
        print("Model will retrain after 1 hour.")
        time.sleep(3600)

# Start the model training in a separate thread
training_thread = threading.Thread(target=train_model)
training_thread.start()
