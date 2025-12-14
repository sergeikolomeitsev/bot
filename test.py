import websocket
import threading

WS_URL = "ws://146.190.89.166:8765/relay"

def on_message(ws, message):
    print(f"RAW MESSAGE:\n{message}\n{'='*30}")

def on_open(ws):
    # Пример подписки на тикер BTCUSDT (если требуется)
    try:
        sub = {"op": "subscribe", "args": ["tickers.BTCUSDT"]}
        ws.send(str(sub).replace("'", '"'))  # Превращаем в JSON строку
        print("Subscribed to tickers.BTCUSDT")
    except Exception as e:
        print(f"ERROR on subscribe: {e}")

def on_error(ws, error):
    print("ERROR:", error)

def on_close(ws, close_status_code, close_msg):
    print("WS CLOSED:", close_status_code, close_msg)

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    t = threading.Thread(target=ws.run_forever, kwargs={"ping_interval": 20})
    t.start()