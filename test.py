import websocket
import threading
import json
import time

WS_URL = "ws://146.190.89.166:8765/relay"  # ваш адрес

def debug_log_ws_message(message):
    print("\n[DEBUG] ------ New message received ------")
    print("[DEBUG] Raw WS message type:", type(message))
    print("[DEBUG] Raw WS message repr:", repr(message)[:500])
    try:
        data = json.loads(message)
        print("[DEBUG] Parsed JSON type:", type(data))
        if isinstance(data, dict):
            print("[DEBUG] Top-level dict keys:", list(data.keys()))
            for k, v in data.items():
                print(f"  key: {k}, type: {type(v)}, value: {repr(v)[:100]}")
                if k in ("kline", "k"):
                    print(f"[DEBUG] Nested '{k}' keys:", list(v.keys()))
                    for nk, nv in v.items():
                        print(f"    nested key: {nk}, type: {type(nv)}, value: {repr(nv)[:100]}")
        elif isinstance(data, list):
            print(f"[DEBUG] List of length {len(data)}. First element type: {type(data[0]) if data else None}")
            if data:
                print("  First element sample:", repr(data[0])[:200])
        else:
            print("[DEBUG] Parsed JSON value:", repr(data)[:300])
    except Exception as e:
        print("[DEBUG] Failed to parse as JSON:", e)

def on_message(ws, message):
    debug_log_ws_message(message)
    # Для краткости печатаем только первые 5 сообщений и закрываем соединение
    if not hasattr(ws, "_msg_count"):
        ws._msg_count = 0
    ws._msg_count += 1
    if ws._msg_count >= 5:
        print("\n[DEBUG] Получено 5 сообщений. Закрытие соединения.")
        ws.close()

def on_error(ws, error):
    print("[WS ERROR]", error)

def on_close(ws, close_status_code, close_msg):
    print("[WS CLOSED]", close_status_code, close_msg)

def on_open(ws):
    print("[WS] Соединение установлено. Жду сообщения...")
    subscribe_msg = {
        "op": "subscribe",
        "args": [
            "kline.1.BTCUSDT",
            "kline.1.ETHUSDT",
            "kline.1.SOLUSDT",
            "kline.1.XRPUSDT",
            "kline.1.BNBUSDT",
        ]
    }
    ws.send(json.dumps(subscribe_msg))
    print("[WS] SUBSCRIBE sent:", subscribe_msg)

if __name__ == "__main__":
    print(f"Connecting to {WS_URL} ...")
    ws = websocket.WebSocketApp(
        WS_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws.run_forever()