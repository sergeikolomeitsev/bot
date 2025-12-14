# ============================================================
# WS PRICE FEED v9.4 — Stable Version with History Buffer and Custom Relay
# ------------------------------------------------------------
# ✔ Stable reconnect loop
# ✔ Filters empty & zero prices
# ✔ Dead-feed detection (no updates)
# ✔ is_alive() used by TradingLoop for safety
# ✔ Thread-safe updates
# ✔ Сохраняет историю цен по каждому тикеру (history buffer)
# ✔ Использует кастомный WS Relay-эндпоинт
# ============================================================

import logging
import time
import json
import websocket
import threading
import ssl   # <-- added for SSL fix


class WSPriceFeed:
    """
    WebSocket price feed for Bybit SPOT (через WS Relay).
    Provides:
        - latest prices in dict
        - last update timestamp
        - dead-feed detection
        - historical price series per symbol (self._history)
    """

    def __init__(self, config):
        self.logger = logging.getLogger("WSPriceFeed")
        self.logger.info("🌐 WSPriceFeed v9.4 initialized")

        self.cfg = config

        # latest prices: {"BTCUSDT": 91350.1, ...}
        self.prices = {}

        # История цен: { "BTCUSDT": [p1, p2, ...] }
        self._history = {}
        self.max_history = 1000  # глубина истории по каждому тикеру

        # timestamp of last received update
        self.last_update = None

        # if no messages for this number of seconds → WS considered dead
        self.dead_interval = 20

        # ------------------------------------------------------------
        # USE CUSTOM RELAY ENDPOINT
        # ------------------------------------------------------------
        self.ws_url = "ws://146.190.89.166:8765/relay"
        self.logger.info(f"Connecting to WS Relay: {self.ws_url}")

        # background WS thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    # =====================================================================
    # PUBLIC API
    # =====================================================================

    def get_prices(self):
        """Return last valid price snapshot (used by MarketDataManager)."""
        return dict(self.prices)

    def is_alive(self):
        """
        WS is alive if:
        - at least one update happened
        - last update was not too long ago
        """
        if self.last_update is None:
            return False
        return (time.time() - self.last_update) < self.dead_interval

    def get_history(self, symbol, depth=500):
        """
        Return last N prices for specified symbol (for strategies and analytics).
        """
        return self._history.get(symbol, [])[-depth:]

    # =====================================================================
    # INTERNAL — MAIN LOOP
    # =====================================================================

    def _run(self):
        """
        Infinite reconnect loop.
        If WS dies → auto reconnect.
        """
        while True:
            try:
                self._connect()
            except Exception as e:
                self.logger.error(f"❌ WS main-loop exception: {e}")
            time.sleep(2)

    # =====================================================================
    # INTERNAL — CONNECT + SUBSCRIBE
    # =====================================================================

    def _connect(self):
        """
        Opens the WebSocket connection and runs it until failure.
        """
        self.logger.info(f"🔌 Connecting to WS: {self.ws_url}")

        ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self.on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        # ------------------------------------------------------------
        # SSL FIX for macOS / Python / websocket-client
        # ------------------------------------------------------------
        ws.run_forever(
            ping_interval=20,
            ping_timeout=10,
            sslopt={
                "cert_reqs": ssl.CERT_NONE,
                "check_hostname": False,
                "ca_certs": None
            }
        )

    # =====================================================================
    # CALLBACKS
    # =====================================================================

    def _on_open(self, ws):
        """Subscribe to all spot symbols defined in config."""
        self.logger.info("✅ WS connected")

        subs = []
        for sym in self.cfg.trading.symbols:
            # for spot: tickers.{symbol}
            subs.append({"op": "subscribe", "args": [f"tickers.{sym}"]})

        for sub in subs:
            ws.send(json.dumps(sub))
        self.logger.info(f"⬆️ Subscribed symbols: {self.cfg.trading.symbols}")

    def on_message(self, ws, message):
        try:
            msg = json.loads(message)
            topic = msg.get("topic", "")
            if topic.startswith("tickers"):
                d = msg.get("data")
                if not isinstance(d, dict):
                    return
                symbol = d.get("symbol")
                price_str = d.get("lastPrice") or d.get("ask1Price") or d.get("bid1Price") or "0"
                try:
                    price = float(price_str)
                except Exception:
                    price = 0
                if not symbol or price == 0:
                    return
                self.prices[symbol] = price
                self.last_update = time.time()
                # --- accumulate history ---
                if symbol not in self._history:
                    self._history[symbol] = []
                self._history[symbol].append(price)
                if len(self._history[symbol]) > self.max_history:
                    self._history[symbol] = self._history[symbol][-self.max_history:]
        except Exception as e:
            self.logger.error(f"WS on_message error: {e}")

    def _on_error(self, ws, error):
        self.logger.error(f"❌ WS error: {error}")

    def _on_close(self, ws, code, msg):
        self.logger.warning(f"🔌 WS closed: {code} {msg}")