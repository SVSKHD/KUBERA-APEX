# Dhan Trading Bot

This trading bot uses the Dhan API to monitor and trade both equities and options based on technical analysis indicators. It dynamically selects the best trades to execute based on the available balance and profit targets.

## Functionalities

1. **Initialization**:
   - Establishes a connection with the Dhan API using provided API credentials.

2. **Data Fetching**:
   - Fetches historical data for equities and options for multiple timeframes.
   - Converts fetched data into a Pandas DataFrame for easy manipulation and analysis.

3. **Indicators Calculation**:
   - Calculates several technical indicators such as RSI, Moving Average, Bollinger Bands, MACD, and ADX for the fetched data.

4. **Signal Generation**:
   - Generates trading signals (BUY, SELL, HOLD) based on calculated indicators.
   - Combines signals from multiple timeframes to generate a final trade signal.

5. **Trade Selection**:
   - Evaluates potential trades for equities and options.
   - Estimates potential profit for each trade.
   - Selects the best trades based on estimated profit.

6. **Trade Execution**:
   - Places orders for the selected trades on the Dhan platform.
   - Monitors active trades and closes them if they hit stop-loss or take-profit levels.

7. **Profit Calculation**:
   - Continuously updates and calculates the daily profit based on closed trades.
   - Stops trading once the daily profit target is reached.

8. **Concurrency**:
   - Utilizes multithreading to handle multiple symbols concurrently.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/dhan-trading-bot.git
    cd dhan-trading-bot
    ```

2. Install required packages:
    ```sh
    pip install pandas requests
    ```

3. Set up your Dhan API credentials in a `.env` file:
    ```sh
    API_KEY=your_api_key
    API_SECRET=your_api_secret
    ACCESS_TOKEN=your_access_token
    ```

4. Update `main_dhan.py` with your trading parameters:
    - Symbols
    - Options symbols (strike price, option type, expiry date)
    - Timeframes
    - Trading parameters (risk percentage, stop-loss pips, movement pips, daily target, initial balance)

## Usage

Run the trading bot:
```sh
python main_dhan.py
