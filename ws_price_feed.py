# ============================================================
# WS PRICE FEED v10.0 — OHLC HISTORY FOR STRATEGY
# ------------------------------------------------------------
# Поддержка: BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT, DOGEUSDT, AVAXUSDT
# Честные свечи (open/high/low/close/volume), auto-subscribe к Bybit relay
# ============================================================

import threading
import time
import json
import websocket
import ssl
import logging

class WSPriceFeed:
    def __init__(self, config):
        self.logger = logging.getLogger("WSPriceFeed")
        self.logger.info("🌐 WSPriceFeed v10.0 initialized")
        self.cfg = config
        self.monitored_symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT", "AVAXUSDT"
        ]
        self.prices = {}  # {"BTCUSDT": 12345.0 ...}
        self._ohlc_history = {sym: [] for sym in self.monitored_symbols}
        self.max_history = 1000
        self.last_update = None
        self.dead_interval = 60
        self.ws_url = "ws://146.190.89.166:8765/relay"
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def get_prices(self):
        return dict(self.prices)

    def is_alive(self):
        if self.last_update is None:
            return False
        seconds_since = time.time() - self.last_update
        alive = seconds_since < self.dead_interval
        return alive

    def get_ohlc_history(self, symbol, depth=500):
        return self._ohlc_history.get(symbol, [])[-depth:]

    def _run(self):
        while True:
            try:
                self._connect()
            except Exception as e:
                self.logger.error(f"❌ WS main-loop exception: {e}")
            time.sleep(2)

    def _connect(self):
        self.logger.info(f"🔌 Connecting to WS: {self.ws_url}")
        ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self.on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        ws.run_forever(
            ping_interval=20,
            ping_timeout=10,
            sslopt={
                "cert_reqs": ssl.CERT_NONE,
                "check_hostname": False,
                "ca_certs": None
            }
        )

    def _on_open(self, ws):
        self.logger.info("✅ WS connected")
        subscribe_msg = {
            "op": "subscribe",
            "args": [
                f"kline.1.{sym}" for sym in self.monitored_symbols
            ]
        }
        ws.send(json.dumps(subscribe_msg))
        self.logger.info(f"[WS] SUBSCRIBE sent: {subscribe_msg}")

    def on_message(self, ws, message):
        data = json.loads(message)
        bars = data.get("data", [])
        topic = data.get("topic", "")
        if data.get("type") in ["snapshot", "update"] and topic.startswith("kline.1."):
            symbol = topic.split(".")[-1]
            # Только для отслеживаемых монет
            if symbol not in self.monitored_symbols:
                return

            ohlc = None  # Определяем ohlc заранее, чтобы избежать ошибки

            # Проверяем, есть ли данные в 'bars'
            if bars:
                for bar in bars:
                    ohlc = {
                        "open": float(bar["open"]),
                        "high": float(bar["high"]),
                        "low": float(bar["low"]),
                        "close": float(bar["close"]),
                        "volume": float(bar.get("volume", 0.0)),
                        "start": bar.get("start"),
                        "end": bar.get("end"),
                        "confirm": bar.get("confirm", False),
                        "timestamp": bar.get("timestamp")
                    }
                    # Не допускаем дубликатов по start
                    if self._ohlc_history[symbol] and bar.get("start"):
                        if self._ohlc_history[symbol][-1].get("start") == bar.get("start"):
                            self._ohlc_history[symbol][-1] = ohlc
                        else:
                            self._ohlc_history[symbol].append(ohlc)
                    else:
                        self._ohlc_history[symbol].append(ohlc)
                    if len(self._ohlc_history[symbol]) > self.max_history:
                        self._ohlc_history[symbol].pop(0)

            if ohlc:  # Проверяем, что ohlc был установлен в цикле
                self.prices[symbol] = ohlc["close"]
                self.last_update = time.time()
            else:
                # Лог предупреждения, если bars пуст или нет ohlc
                self.logger.warning(f"No valid OHLC data for symbol {symbol}. Prices not updated.")

    def _on_error(self, ws, error):
        self.logger.error(f"[WS ERROR] {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self.logger.info(f"[WS CLOSED] {close_status_code} {close_msg}")
