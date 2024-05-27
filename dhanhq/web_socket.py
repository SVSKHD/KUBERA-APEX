import websocket
import json


def on_message(ws, message):
    print("Received message:", message)
    # Process the message here


def on_error(ws, error):
    print("WebSocket error:", error)


def on_close(ws):
    print("WebSocket closed")


def on_open(ws):
    print("WebSocket connection opened")
    # Subscribe to market data
    subscribe_message = {
        "action": "subscribe",
        "symbols": ["NSE:RELIANCE", "NSE:TCS"]  # Add symbols you want to subscribe to
    }
    ws.send(json.dumps(subscribe_message))


def connect_websocket(api_key, api_secret, access_token):
    websocket_url = "wss://api.dhan.co/v1/live"  # Replace with the actual WebSocket URL
    headers = {
        "api-key": api_key,
        "api-secret": api_secret,
        "access-token": access_token
    }
    ws = websocket.WebSocketApp(
        websocket_url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


